# KS-TRACE: P1-WEBHOOK-03 | test: signature verification, event dispatch
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from patchward import webhook


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture(autouse=True)
def _reset_rate_limit_state() -> None:
    """
    BACKLOG 5's rate limiter is module-level state (a plain deque, by
    design — see webhook.py's docstring). Without an explicit reset,
    tests would leak timestamps into each other's counts in whatever
    order pytest happens to run them. Autouse so every test in this
    file — not just the rate-limit-specific ones — starts from zero.
    """
    webhook._rate_limit_timestamps.clear()
    yield
    webhook._rate_limit_timestamps.clear()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setattr(webhook, "_DB_PATH", tmp_path / "webhook_state.db")
    return TestClient(webhook.app)


def test_missing_signature_header_rejected(client: TestClient) -> None:
    response = client.post("/webhooks/github", json={"zen": "hi"}, headers={"X-GitHub-Event": "ping"})
    assert response.status_code == 401


def test_wrong_signature_rejected(client: TestClient) -> None:
    body = json.dumps({"zen": "hi"}).encode("utf-8")
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=deadbeef",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_ping_event_with_valid_signature_returns_pong(client: TestClient) -> None:
    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


def test_installation_created_event_persists_installation(client: TestClient) -> None:
    payload = {
        "action": "created",
        "installation": {"id": 42, "account": {"login": "acme", "type": "Organization"}},
        "repositories": [{"full_name": "acme/backend"}],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "installation",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200

    from patchward.installations_db import list_active_repos, open_db

    conn = open_db(webhook._DB_PATH)
    try:
        row = conn.execute("SELECT * FROM installations WHERE id = ?", (42,)).fetchone()
        assert row["account_login"] == "acme"
        assert list_active_repos(conn, 42) == ["acme/backend"]
    finally:
        conn.close()


def test_unrecognized_event_is_acknowledged_not_rejected(client: TestClient) -> None:
    body = json.dumps({"anything": True}).encode("utf-8")
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "some_future_event_type",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_delivery_id_logged_for_every_handled_delivery(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """X-GitHub-Delivery is captured in the structured log line (BACKLOG 5)."""
    import logging

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    with caplog.at_level(logging.INFO, logger="patchward.webhook"):
        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": signature,
                "X-GitHub-Delivery": "test-delivery-id-123",
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 200
    assert any(
        "test-delivery-id-123" in rec.message for rec in caplog.records
    ), f"Expected delivery id in a log record. Got: {[r.message for r in caplog.records]}"


def test_missing_delivery_header_does_not_crash(client: TestClient) -> None:
    """Absent X-GitHub-Delivery must not raise — logs an empty sentinel."""
    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


def test_rate_limit_returns_429_after_threshold(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BACKLOG 5: sliding-window limiter caps requests per window."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", "3")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", "60")

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json",
    }

    statuses = [client.post("/webhooks/github", content=body, headers=headers).status_code for _ in range(3)]
    assert statuses == [200, 200, 200]

    fourth = client.post("/webhooks/github", content=body, headers=headers)
    assert fourth.status_code == 429


def test_rate_limit_window_slides_after_expiry(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A request outside the window doesn't count against the limit."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", "1")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", "60")

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json",
    }

    first = client.post("/webhooks/github", content=body, headers=headers)
    assert first.status_code == 200

    second = client.post("/webhooks/github", content=body, headers=headers)
    assert second.status_code == 429

    # Simulate the window having fully elapsed by clearing the recorded
    # timestamp directly rather than sleeping the test — this is the
    # same state _check_rate_limit's own sliding-window eviction would
    # produce once `time.monotonic() - recorded_ts > window_seconds`.
    webhook._rate_limit_timestamps.clear()

    third = client.post("/webhooks/github", content=body, headers=headers)
    assert third.status_code == 200


def test_oversized_payload_rejected_413_via_content_length(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BACKLOG 5: Content-Length over the configured max is rejected before signature checks run."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", "10")

    body = json.dumps({"zen": "hi"}).encode("utf-8")  # well over 10 bytes
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 413


def test_body_within_limit_still_processed_normally(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity check: the size limit doesn't false-positive on ordinary payloads."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", str(25 * 1024 * 1024))

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    signature = _sign("test-secret", body)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


def _spy_check_body_size(monkeypatch: pytest.MonkeyPatch) -> list:
    """
    Wrap the real `_check_body_size` (the Content-Length fast-path check) so
    every call's argument and whether it raised is recorded, while still
    running the real function underneath. This lets a test assert, from
    inside the actual request that ran, exactly what Content-Length value
    the fast path saw and that it did NOT raise — proving any 413 that
    follows came from the second, post-read check (webhook.py L264-269),
    not this one. A plain no-op monkeypatch would only prove "a 413
    happened with the fast path disabled," which is weaker: it wouldn't
    confirm what Content-Length the request actually carried. Recording the
    call arguments while still delegating to the real implementation proves
    both facts at once.
    """
    calls: list = []
    original = webhook._check_body_size

    def spy(content_length_header: str | None) -> None:
        calls.append(content_length_header)
        original(content_length_header)  # real check still runs — must not raise here

    monkeypatch.setattr(webhook, "_check_body_size", spy)
    return calls


def test_oversized_payload_no_content_length_rejected_via_second_check(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    BACKLOG 5 follow-up: webhook.py's post-read defense-in-depth body-size
    check (L264-269) exists specifically for requests that omit
    Content-Length (e.g. chunked transfer-encoding) or lie about it — the
    existing test_oversized_payload_rejected_413_via_content_length only
    exercises the Content-Length fast path (_check_body_size), never this
    second check. Sending the body via a generator forces httpx to use
    chunked transfer-encoding with no Content-Length header at all
    (confirmed via a standalone diagnostic: content=<generator> produces
    `transfer-encoding: chunked` and no `content-length` header on the
    request FastAPI/Starlette actually receives).
    """
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", "100")
    calls = _spy_check_body_size(monkeypatch)

    def gen():
        yield b"x" * 500

    response = client.post(
        "/webhooks/github",
        content=gen(),
        headers={"X-GitHub-Event": "ping"},
    )

    assert calls == [None], (
        f"expected the fast-path check to see NO Content-Length header "
        f"(proving it was a no-op and could not have produced the 413), got {calls}"
    )
    assert response.status_code == 413


def test_oversized_payload_lying_content_length_rejected_via_second_check(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Break-case beyond a merely-absent header: a client that sends a small,
    well-formed but WRONG Content-Length while actually streaming a larger
    body. The fast path only ever inspects the header value (it never reads
    the body), so a lying header sails through it; the second check reads
    the real body and must catch it.
    """
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", "100")
    calls = _spy_check_body_size(monkeypatch)

    body = b"x" * 500
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={"X-GitHub-Event": "ping", "Content-Length": "10"},
    )

    assert calls == ["10"], (
        f"expected the fast-path check to see the lying '10' Content-Length "
        f"header and pass it (10 is not > 100), got {calls}"
    )
    assert response.status_code == 413


def test_oversized_body_no_content_length_boundary_exact_vs_plus_one(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Data-boundary check on the second check specifically: a body of exactly
    `PATCHWARD_WEBHOOK_MAX_BODY_BYTES` bytes must NOT be rejected (strict
    `>`, not `>=`); one byte more must be. Both cases go through the
    no-Content-Length (chunked) path so the fast path stays a confirmed
    no-op throughout (asserted via the spy) and the boundary behavior
    being proven is genuinely the second check's, not the fast path's.
    The "no rejection" case is asserted as a full valid 200 (correct
    signature, correct response body) rather than merely "not 413", so a
    coincidental different failure can't masquerade as a pass.
    """
    calls = _spy_check_body_size(monkeypatch)
    payload = {"zen": "hi", "pad": "y" * 500}
    body = json.dumps(payload).encode("utf-8")
    signature = _sign("test-secret", body)
    exact = len(body)

    # Case 1: max == exact body length -> must be accepted (200, real pong).
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", str(exact))

    def gen_at_limit():
        yield body

    ok_response = client.post(
        "/webhooks/github",
        content=gen_at_limit(),
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert ok_response.status_code == 200
    assert ok_response.json() == {"status": "pong"}

    # Case 2: max == exact body length - 1 -> body is now 1 byte over -> 413.
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", str(exact - 1))

    def gen_over_by_one():
        yield body

    over_response = client.post(
        "/webhooks/github",
        content=gen_over_by_one(),
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert over_response.status_code == 413

    assert calls == [None, None], (
        f"expected the fast-path check to see NO Content-Length header on "
        f"either boundary request, got {calls}"
    )


def test_healthz() -> None:
    client = TestClient(webhook.app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_failed_hmac_does_not_consume_rate_limit_budget(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Phase 9 security-boundary change: the limiter now runs AFTER
    _verify_signature, so a request with a bad signature is rejected 401
    before the limiter is ever reached and cannot consume the window.
    Proof: with the budget set to 2, fire 5 invalid-signature requests —
    all must be 401, never 429 (a 429 would mean the limiter was hit
    pre-auth) — and the rate-limit deque must stay empty; then a single
    VALID signed request must still succeed with 200. Under the old
    pre-auth ordering the 5 junk requests would have filled the window and
    the valid delivery would have been starved into a 429.
    """
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", "60")

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    bad_headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": "sha256=deadbeef",
        "Content-Type": "application/json",
    }
    invalid_statuses = [
        client.post("/webhooks/github", content=body, headers=bad_headers).status_code
        for _ in range(5)
    ]
    assert invalid_statuses == [401, 401, 401, 401, 401], (
        f"failed-HMAC requests must all be 401 (never 429) — a 429 would mean the "
        f"limiter was reached before signature verification. Got {invalid_statuses}"
    )
    assert len(webhook._rate_limit_timestamps) == 0, (
        "failed-HMAC requests must not have appended to the rate-limit deque"
    )

    good_headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": _sign("test-secret", body),
        "Content-Type": "application/json",
    }
    valid = client.post("/webhooks/github", content=body, headers=good_headers)
    assert valid.status_code == 200, (
        f"a valid signed delivery after a flood of junk must still succeed, got {valid.status_code}"
    )
    assert valid.json() == {"status": "pong"}


def test_malformed_numeric_env_falls_back_to_default_not_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Bundled low finding: a malformed numeric override env var used to raise
    inside the handler and 500 every request. Each parse now falls back to
    its documented default (fail-safe). Set all three overrides to garbage
    and assert (a) the helpers return their defaults and (b) a normal valid
    delivery still returns 200 rather than erroring.
    """
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", "not-a-number")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", "abc")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", "huge")

    assert webhook._rate_limit_max_requests() == 60
    assert webhook._rate_limit_window_seconds() == 60.0
    assert webhook._max_body_bytes() == 25 * 1024 * 1024

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": _sign("test-secret", body),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


@pytest.mark.parametrize("bad_window", ["inf", "nan", "-inf", "-1", "0"])
def test_window_seconds_out_of_range_falls_back_to_default(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, bad_window: str
) -> None:
    """
    Phase 9 hardening: float() accepts inf/nan/-inf without raising, so the
    old `except ValueError` guard let them through — an infinite window never
    expires a timestamp and 429s forever once full; a zero/negative window is
    nonsensical. Each must now fall back to the default AND the endpoint must
    still serve a normal 200.
    """
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", bad_window)
    assert webhook._rate_limit_window_seconds() == 60.0

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": _sign("test-secret", body),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


@pytest.mark.parametrize("bad_max", ["0", "-5"])
def test_rate_limit_max_out_of_range_falls_back_to_default(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, bad_max: str
) -> None:
    """A max < 1 (zero/negative) would 429 the very first request forever — must default."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", bad_max)
    assert webhook._rate_limit_max_requests() == 60

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": _sign("test-secret", body),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


@pytest.mark.parametrize("bad_bytes", ["0", "-5"])
def test_max_body_bytes_out_of_range_falls_back_to_default(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, bad_bytes: str
) -> None:
    """A <1 byte cap makes every request fail the size check (413 outage) — must default."""
    monkeypatch.setenv("PATCHWARD_WEBHOOK_MAX_BODY_BYTES", bad_bytes)
    assert webhook._max_body_bytes() == 25 * 1024 * 1024

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": _sign("test-secret", body),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "pong"}


def test_infinite_window_env_still_expires_limiter_recovers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Strong proof the inf hole is closed: not merely "no 500", but that the
    limiter still RECOVERS. With WINDOW="inf" guarded back to the finite 60s
    default and MAX=1, fill the window (one request), confirm the next is 429,
    then age the recorded timestamp past the window and confirm a later
    request succeeds again. If "inf" had leaked through unguarded,
    window_start would be -inf, the timestamp could never evict, and the
    third request would be a permanent 429 instead of the 200 asserted here.
    """
    import time

    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS", "inf")
    monkeypatch.setenv("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX", "1")

    body = json.dumps({"zen": "hi"}).encode("utf-8")
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": _sign("test-secret", body),
        "Content-Type": "application/json",
    }

    first = client.post("/webhooks/github", content=body, headers=headers)
    assert first.status_code == 200

    second = client.post("/webhooks/github", content=body, headers=headers)
    assert second.status_code == 429

    # Age the single recorded timestamp to well beyond the (defaulted, finite)
    # 60s window. With the guard, eviction removes it and the next request is
    # accepted; without the guard (window == inf) it could never be evicted.
    assert len(webhook._rate_limit_timestamps) == 1
    webhook._rate_limit_timestamps[0] = time.monotonic() - 120.0

    third = client.post("/webhooks/github", content=body, headers=headers)
    assert third.status_code == 200
    assert third.json() == {"status": "pong"}


# ---------------------------------------------------------------------------
# BACKLOG 28 — fail-loud-at-startup credential shape guard.
# Validates SHAPE of credentials that are set; absence is a warning, not a
# failure. Existing tests above use TestClient WITHOUT the `with` context
# manager, so they never trigger the lifespan and are unaffected by this guard.
# ---------------------------------------------------------------------------

# A realistic, > 20-char valid-shaped Anthropic key for the "accepts" path and
# as filler where the Anthropic value is not the subject under test. BACKLOG 28
# v2 (F3) adds a minimum-length check, so short stubs like "sk-ant-ok" no longer
# pass the guard and cannot be used as innocuous filler.
_VALID_ANTHROPIC_KEY = "sk-ant-api03-" + "a" * 24


def _real_private_key_pem() -> bytes:
    """A genuine, parseable RSA private key PEM (generated fresh — never a real
    secret). BACKLOG 28 v2 (F1) replaces the guard's substring check with an
    actual load_pem_private_key() parse, so the "accepts" tests must use a key
    that really parses, not a header wrapped around filler bytes."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


# Generated once per module run — RSA keygen is comparatively expensive.
_VALID_PRIVATE_KEY_PEM = _real_private_key_pem()


def _clear_app_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in (
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY_B64",
        "GITHUB_APP_PRIVATE_KEY",
    ):
        monkeypatch.delenv(k, raising=False)


def test_startup_rejects_non_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-110-char-credential-from-a-different-service")
    _clear_app_creds(monkeypatch)
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


def test_startup_rejects_short_stub_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "req_011Cd")  # 9-char stub shape
    _clear_app_creds(monkeypatch)
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


def test_startup_accepts_valid_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    webhook._validate_credential_shapes()  # must not raise


def test_startup_allows_absent_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _clear_app_creds(monkeypatch)
    webhook._validate_credential_shapes()  # absence warns, does not raise


def test_startup_rejects_non_numeric_app_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv("GITHUB_APP_ID", "not-numeric")
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


def test_startup_rejects_bad_b64_private_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    # valid base64, but does not decode to a PEM private key
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(b"not a pem").decode()
    )
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


def test_startup_accepts_valid_b64_private_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    # A genuine, parseable PEM — the guard now really parses it (BACKLOG 28 v2).
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64",
        base64.b64encode(_VALID_PRIVATE_KEY_PEM).decode(),
    )
    monkeypatch.setenv("GITHUB_APP_ID", "123456")
    webhook._validate_credential_shapes()  # must not raise


def test_startup_error_never_contains_credential_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_value = "wrongkey-abcdef0123456789-should-never-appear"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret_value)
    _clear_app_creds(monkeypatch)
    with pytest.raises(webhook.StartupCredentialError) as excinfo:
        webhook._validate_credential_shapes()
    assert secret_value not in str(excinfo.value)


def test_lifespan_aborts_startup_on_malformed_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entering the app through its lifespan raises on a malformed key —
    the production fail-loud path (the `with` context triggers startup)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-an-anthropic-key")
    _clear_app_creds(monkeypatch)
    with pytest.raises(webhook.StartupCredentialError):
        with TestClient(webhook.app):
            pass


# ---------------------------------------------------------------------------
# BACKLOG 28 v2 — regression tests for the adversarial-review findings.
# F1: substring check accepted a valid header wrapped around garbage.
# F2: the guard's base64 decode diverged from the real consumer's decode.
# These would have FAILED against v1 and must PASS against v2.
# ---------------------------------------------------------------------------

def test_startup_rejects_bad_raw_private_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A raw GITHUB_APP_PRIVATE_KEY that CONTAINS the 'PRIVATE KEY' substring
    but is not a parseable PEM must now be rejected (v1 accepted it)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY",
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "this is not real base64 key material\n"
        "-----END RSA PRIVATE KEY-----\n",
    )
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


def test_startup_rejects_invalid_b64_private_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Input that is not valid base64 at all must be rejected with a clear
    message (the guard's decode now mirrors the consumer's b64decode)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", "not valid base64 %%%")
    with pytest.raises(webhook.StartupCredentialError) as excinfo:
        webhook._validate_credential_shapes()
    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)


def test_startup_rejects_unparseable_b64_pem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid base64 that decodes to UTF-8 text which is NOT a parseable PEM
    must be rejected — the F1 substring check is gone from the B64 branch too."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    payload = b"this is valid utf-8 text but is definitely not a PEM key"
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(payload).decode()
    )
    with pytest.raises(webhook.StartupCredentialError) as excinfo:
        webhook._validate_credential_shapes()
    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)


def test_junk_pem_that_matches_substring_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact junk PEM from the adversarial review — a well-formed header
    and footer wrapped around 'GARBAGE'. It satisfies the old
    `"PRIVATE KEY" in raw_key` substring check (so v1 ACCEPTED it) but is not
    a parseable private key. This test is the proof F1 is actually closed."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    junk_pem = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
    assert "PRIVATE KEY" in junk_pem  # confirms it would pass the v1 substring gate
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", junk_pem)
    with pytest.raises(webhook.StartupCredentialError):
        webhook._validate_credential_shapes()


# ---------------------------------------------------------------------------
# BACKLOG 28 v3 — regression tests for the second adversarial-review findings.
# F-A: the guard accepted ANY parseable private key, not RSA specifically;
#      an EC/Ed25519 key parses but cannot sign the RS256 App JWT.
# F-B: the guard validated BOTH raw and B64 independently, so a valid raw
#      key + stale/garbage B64 caused a false boot failure — the consumer
#      reads raw first and never looks at B64.
# F-C: a discriminating B64-branch junk-PEM test (payload that would have
#      passed the v1 substring check) was missing.
# These would have FAILED against v2 and must PASS against v3.
# ---------------------------------------------------------------------------


def _real_ec_private_key_pem() -> bytes:
    """A genuine, parseable EC (non-RSA) private key PEM (generated fresh —
    never a real secret). It loads cleanly via load_pem_private_key() but is
    NOT an rsa.RSAPrivateKey, so the v3 guard must reject it (F-A)."""
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_startup_rejects_valid_but_non_rsa_private_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-A: a real EC private key parses cleanly but cannot sign RS256, so the
    guard must REJECT it. v2 (isinstance check absent) ACCEPTED it — this is the
    regression proof. Asserted for BOTH the raw and the B64 branch."""
    ec_pem = _real_ec_private_key_pem()

    # Raw branch.
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", ec_pem.decode("utf-8"))
    with pytest.raises(webhook.StartupCredentialError) as excinfo_raw:
        webhook._validate_credential_shapes()
    assert "RSA" in str(excinfo_raw.value)

    # B64 branch (raw cleared so the consumer — and the guard — fall back to it).
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(ec_pem).decode()
    )
    with pytest.raises(webhook.StartupCredentialError) as excinfo_b64:
        webhook._validate_credential_shapes()
    assert "RSA" in str(excinfo_b64.value)


def test_startup_ignores_stale_b64_when_raw_key_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-B: the consumer (github_app_auth._load_private_key) reads RAW first and
    returns it outright — B64 is never consulted when RAW is present. So a valid
    RAW key paired with a deliberately garbage B64 value must still BOOT (guard
    ACCEPTS). v2 validated B64 independently and raised a spurious error here —
    a false boot failure. This is the regression proof for F-B."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    monkeypatch.setenv("GITHUB_APP_ID", "123456")
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY", _VALID_PRIVATE_KEY_PEM.decode("utf-8")
    )
    # Stale/garbage B64 the consumer will never read.
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", "not valid base64 %%%")
    webhook._validate_credential_shapes()  # must not raise


def test_junk_pem_with_substring_via_b64_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-C: the exact junk PEM ('-----BEGIN PRIVATE KEY-----\\nGARBAGE\\n-----END
    PRIVATE KEY-----') base64-encoded into the B64 variable. Its decoded form
    satisfies the old v1 `"PRIVATE KEY" in ...` substring check (v1 ACCEPTED it)
    but is not a parseable private key, so v3 must REJECT it. This is the
    discriminating B64-branch test that was missing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", _VALID_ANTHROPIC_KEY)
    _clear_app_creds(monkeypatch)
    junk_pem = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
    assert "PRIVATE KEY" in junk_pem  # confirms it would pass the v1 substring gate
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(junk_pem.encode()).decode()
    )
    with pytest.raises(webhook.StartupCredentialError) as excinfo:
        webhook._validate_credential_shapes()
    assert "GITHUB_APP_PRIVATE_KEY_B64" in str(excinfo.value)
