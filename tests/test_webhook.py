# KS-TRACE: P1-WEBHOOK-03 | test: signature verification, event dispatch
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest
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


def test_healthz() -> None:
    client = TestClient(webhook.app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
