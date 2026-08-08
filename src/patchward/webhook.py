# KS-TRACE: P1-WEBHOOK-03 | assumption: GITHUB_WEBHOOK_SECRET is set as
# a platform secret and matches the value configured on the GitHub App's
# webhook settings page | test: test_webhook.py
"""
GitHub App + Marketplace webhook receiver.

This is the v0 scope (see ADR-030 in memory/architectural_decisions.md):
a single receiver that (a) verifies every inbound webhook's
signature before touching the payload, (b) keeps installation/repo/
purchase state in installations_db.py, and (c) triggers the existing
scan -> fix-gen -> verify -> PR pipeline (pipeline.run_repo_pipeline) for
a repo using a freshly-minted, 1-hour Installation Access Token instead
of a long-lived PAT.

Deliberately NOT in this version (see ADR-030):
  - A real task queue. Scan runs are dispatched via FastAPI's
    BackgroundTasks, which is fine for a handful of installations but
    will need to move to a proper queue (e.g. Redis + arq, or SQS) once
    volume or run-time makes in-process background tasks unreliable.
  - Postgres. installations_db.py is SQLite; swapping the backing store
    is isolated to that one file.
  - Any payment-processing code. GitHub is merchant of record вЂ” this
    file only ever reacts to marketplace_purchase webhook events to
    keep is_entitled() current; it never calls a payments API directly.
"""
from __future__ import annotations

import asyncio
import base64
import collections
import hashlib
import hmac
import logging
import math
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from patchward import installations_db as idb
from patchward.config import (
    BatchConfig,
    FixGenConfig,
    GithubConfig,
    ModelsConfig,
    RepoConfig,
    PatchwardConfig,
    VerifierConfig,
)
from patchward.credential_proxy import (
    CredentialProxy,
    register_runtime_credential,
    scrub_text,
)
from patchward.git_credentials import (
    credential_env,
    credential_helper_args,
    tokenless_clone_url,
)
from patchward.github_app_auth import (
    GitHubAppAuthError,
    exchange_for_installation_token,
)
from patchward.pipeline import run_repo_pipeline
from patchward.run_log import RunLog

logger = logging.getLogger(__name__)


class StartupCredentialError(RuntimeError):
    """Raised at process startup when a configured credential is present but
    malformed. Deliberately fails the webhook's boot rather than letting a
    broken secret pass silently and surface as a 401/500 on the first real
    request (BACKLOG 28)."""


# KS-TRACE: BACKLOG 28 вЂ” fail-loud-at-startup credential shape guard.
# The prior guard (`get_client_credentials()` + `if not anthropic_key`) rejected
# only FALSY values, so a present-but-wrong secret passed startup and failed on
# the FIRST pipeline request вЂ” after verify, deep inside a background task.
# Three different broken ANTHROPIC_API_KEY values passed that check across two
# days (a 9-char stub, a 110-char foreign credential, and a third rejected on
# 2026-07-29). This validates the SHAPE of each credential that is set and
# raises before the server accepts traffic.
#
# Policy (deliberately conservative, to avoid false boot failures):
#   * A credential that is SET but malformed  -> raise (fail the boot).
#   * A credential that is ABSENT             -> warn only; presence is still
#     enforced at point of use (signature check / pipeline guard).
# Whether ABSENCE should also fail the boot, and whether /healthz should assert
# validity, are open product decisions (see BACKLOG 28) and are NOT decided here.
#
# No credential VALUE (or any substring of one) is ever logged or raised.
def _validate_credential_shapes() -> None:
    errors: list[str] = []

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        if not anthropic_key.startswith("sk-ant-"):
            errors.append(
                "ANTHROPIC_API_KEY is set but does not begin with the expected "
                "'sk-ant-' prefix"
            )
        elif len(anthropic_key) < 20:
            # F3 (BACKLOG 28 v2): a value with the right prefix but far too
            # short to be a real key (e.g. a truncated paste or an "sk-ant-ok"
            # stub). Floor kept deliberately low вЂ” real keys are ~100+ chars,
            # so this never rejects a genuine credential.
            errors.append(
                "ANTHROPIC_API_KEY is set but is too short to be a valid key"
            )
    else:
        logger.warning("[webhook] ANTHROPIC_API_KEY is not set at startup")

    app_id = os.environ.get("GITHUB_APP_ID", "").strip()
    if app_id and not (app_id.isascii() and app_id.isdigit()):
        # F4 (BACKLOG 28 v2): str.isdigit() returns True for non-ASCII digit
        # characters (e.g. superscripts or digits from other scripts) that are
        # NOT usable as a GitHub App ID. Require ASCII decimal digits only.
        errors.append("GITHUB_APP_ID is set but is not a numeric App ID")

    # F-B (BACKLOG 28 v3): mirror the consumer's ACTUAL precedence
    # (github_app_auth.py:_load_private_key, lines 47-52): RAW is read
    # first and, when present, returned outright вЂ” B64 is NEVER consulted.
    # Only when RAW is absent does the consumer fall back to B64. The prior
    # (v2) guard validated BOTH variables independently, so a valid RAW key
    # paired with a stale/garbage B64 value produced a spurious B64 error and
    # a false boot failure over a value that would never be read. Validate
    # exactly the variable the consumer would use, in the same order.
    raw_key = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
    b64_key = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
    if raw_key:
        # F1 (BACKLOG 28 v2): actually attempt to parse the PEM. The prior
        # `"PRIVATE KEY" in raw_key` substring check accepted a valid-looking
        # header wrapped around a garbage body (the adversarial junk-PEM repro).
        try:
            key = load_pem_private_key(
                raw_key.encode("utf-8"),
                password=None,
                backend=default_backend(),
            )
        except Exception:
            errors.append(
                "GITHUB_APP_PRIVATE_KEY is set but is not a valid PEM private key"
            )
        else:
            # F-A (BACKLOG 28 v3): parseability is not enough. GitHub Apps
            # sign with RS256, which REQUIRES an RSA key; a well-formed EC or
            # Ed25519 key parses cleanly but cannot sign a valid App JWT, so
            # the boot must reject it here rather than fail at first use.
            if not isinstance(key, rsa.RSAPrivateKey):
                errors.append(
                    "GITHUB_APP_PRIVATE_KEY is set but is not an RSA private "
                    "key (GitHub Apps require RSA for RS256 signing)"
                )
    elif b64_key:
        # F2 (BACKLOG 28 v2): mirror the real consumer's decode EXACTLY
        # (github_app_auth.py:50-52) вЂ” same .strip(), same base64.b64decode()
        # with the default validate flag (validate=False), same .decode("utf-8"),
        # in the same order вЂ” so the guard accepts/rejects precisely what the
        # consumer can/cannot use. A stricter decode here (e.g. validate=True)
        # would reject values the consumer accepts and cause false boot failures.
        try:
            decoded_pem = base64.b64decode(b64_key).decode("utf-8")
        except Exception:
            errors.append(
                "GITHUB_APP_PRIVATE_KEY_B64 is set but could not be base64-decoded "
                "to UTF-8 text (does not match the consumer's decode)"
            )
        else:
            # F1 (BACKLOG 28 v2): actually parse the PEM instead of a substring
            # check, so a well-formed header wrapped around garbage is rejected.
            try:
                key = load_pem_private_key(
                    decoded_pem.encode("utf-8"),
                    password=None,
                    backend=default_backend(),
                )
            except Exception:
                errors.append(
                    "GITHUB_APP_PRIVATE_KEY_B64 is set but is not a valid PEM "
                    "private key"
                )
            else:
                # F-A (BACKLOG 28 v3): enforce RSA specifically, consistently
                # with the raw branch вЂ” a parseable non-RSA key cannot sign RS256.
                if not isinstance(key, rsa.RSAPrivateKey):
                    errors.append(
                        "GITHUB_APP_PRIVATE_KEY_B64 is set but is not an RSA "
                        "private key (GitHub Apps require RSA for RS256 signing)"
                    )

    if not os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip():
        logger.warning("[webhook] GITHUB_WEBHOOK_SECRET is not set at startup")

    if errors:
        # Names + failure kinds only вЂ” never a value or any part of one.
        joined = "; ".join(errors)
        logger.error("[webhook] startup credential validation failed: %s", joined)
        raise StartupCredentialError(joined)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # BACKLOG 28: validate credential SHAPES before the server accepts traffic.
    # Raising here aborts startup loudly (uvicorn logs + failed health check)
    # instead of the process appearing healthy over an unusable secret.
    _validate_credential_shapes()
    yield


app = FastAPI(title="Patchward Webhook Receiver", lifespan=_lifespan)

_DB_PATH = Path(os.environ.get("PATCHWARD_WEBHOOK_DB", "runs/webhook_state.db"))

# BACKLOG 5 (Phase 9 Exposure Gate) вЂ” request body size limit.
# GitHub's own hard cap on webhook payloads is 25 MB (a larger event
# simply never gets delivered вЂ” see
# https://docs.github.com/en/webhooks/webhook-events-and-payloads),
# so a limit at that same ceiling never rejects a legitimate delivery
# and still bounds worst-case memory use per request. Read as a
# function (not a module-level constant) so tests can override it via
# `monkeypatch.setenv` without needing to reload the module.
_DEFAULT_MAX_BODY_BYTES = 25 * 1024 * 1024


def _max_body_bytes() -> int:
    # Uniform guard shape across the three numeric-override parsers
    # (_max_body_bytes / _rate_limit_max_requests / _rate_limit_window_
    # seconds): read raw -> absent means default -> parse (unparseable
    # means default) -> RANGE-validate (out-of-range means default). A
    # malformed OR out-of-range override must never reach the request
    # path: an int()/float() that raised would 500 every request, and a
    # <1 byte cap would make every request fail the size check (a silent
    # outage). Fall back to the documented default in every bad case,
    # fail-safe direction; valid in-range values are returned unchanged.
    raw = os.environ.get("PATCHWARD_WEBHOOK_MAX_BODY_BYTES")
    if raw is None:
        return _DEFAULT_MAX_BODY_BYTES
    try:
        value = int(raw)
    except ValueError:
        value = None
    if value is None or value < 1:
        logger.warning(
            "[webhook] invalid PATCHWARD_WEBHOOK_MAX_BODY_BYTES=%r "
            "(must be an integer >= 1) вЂ” using default %d",
            raw,
            _DEFAULT_MAX_BODY_BYTES,
        )
        return _DEFAULT_MAX_BODY_BYTES
    return value


def _check_body_size(content_length_header: str | None) -> None:
    """
    Reject oversized deliveries by Content-Length before the body is read,
    when the client sends that header (GitHub always does). This is a
    fast-path check only вЂ” a client omitting or lying about
    Content-Length (e.g. chunked transfer-encoding) is still caught by
    the second, post-read check in github_webhook, at the cost of that
    request's bytes already having been buffered into memory by
    Starlette. Full protection against that residual case would need a
    streaming ASGI-level body limit, deliberately out of scope for this
    v0 pass (see ADR-030's "deliberately not in this version" list).
    """
    if content_length_header is None:
        return
    try:
        content_length = int(content_length_header)
    except ValueError:
        return
    if content_length > _max_body_bytes():
        raise HTTPException(status_code=413, detail="Payload too large")


# BACKLOG 5 вЂ” rate limiting on /webhooks/github. The limiter is called
# AFTER _verify_signature in the handler (Phase 9 security-boundary
# change), so it counts only HMAC-valid, genuinely-from-GitHub requests.
# An unauthenticated flood is rejected at 401 before it ever reaches the
# limiter and therefore cannot consume the budget вЂ” that closes the
# starvation vector where anonymous traffic filling a shared window would
# push GitHub's real deliveries into 429s and, via GitHub's
# consecutive-non-2xx auto-disable, risk the webhook being turned off.
# The residual cost of an unauthenticated flood (buffering + one HMAC per
# request) is bounded by the body-size cap above and consciously accepted
# at v0 scope, not re-solved with a second pre-auth limiter (ADR-030).
# Single Fly machine, scale-to-zero (fly.toml), no shared store between
# instances by design (ADR-030) вЂ” an in-memory sliding-window counter is
# consistent with that same v0 scope, not a compromise pending a "real"
# implementation. This bounds a runaway/replay flood of otherwise-valid
# GitHub deliveries; it is not a per-installation fairness mechanism.
_RATE_LIMIT_MAX_REQUESTS_DEFAULT = 60
_RATE_LIMIT_WINDOW_SECONDS_DEFAULT = 60.0

_rate_limit_timestamps: collections.deque[float] = collections.deque()


def _rate_limit_max_requests() -> int:
    # Same guard shape as _max_body_bytes. A max < 1 (zero or negative)
    # would make _check_rate_limit reject on the very first request and
    # never accept again вЂ” a permanent-429 outage вЂ” so it falls back to
    # the default just like an unparseable value.
    raw = os.environ.get("PATCHWARD_WEBHOOK_RATE_LIMIT_MAX")
    if raw is None:
        return _RATE_LIMIT_MAX_REQUESTS_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        value = None
    if value is None or value < 1:
        logger.warning(
            "[webhook] invalid PATCHWARD_WEBHOOK_RATE_LIMIT_MAX=%r "
            "(must be an integer >= 1) вЂ” using default %d",
            raw,
            _RATE_LIMIT_MAX_REQUESTS_DEFAULT,
        )
        return _RATE_LIMIT_MAX_REQUESTS_DEFAULT
    return value


def _rate_limit_window_seconds() -> float:
    # Same guard shape as _max_body_bytes, with one extra hazard: float()
    # accepts "inf"/"-inf"/"nan" without raising, and those are NOT caught
    # by `except ValueError`. An infinite window would make the limiter's
    # sliding-window eviction never expire a timestamp, so once the budget
    # filled it would 429 forever. math.isfinite() rejects inf/-inf/nan;
    # `<= 0` rejects zero and negatives. Any of those -> documented default.
    raw = os.environ.get("PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS")
    if raw is None:
        return _RATE_LIMIT_WINDOW_SECONDS_DEFAULT
    try:
        value = float(raw)
    except ValueError:
        value = None
    if value is None or not math.isfinite(value) or value <= 0:
        logger.warning(
            "[webhook] invalid PATCHWARD_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS=%r "
            "(must be a finite number > 0) вЂ” using default %s",
            raw,
            _RATE_LIMIT_WINDOW_SECONDS_DEFAULT,
        )
        return _RATE_LIMIT_WINDOW_SECONDS_DEFAULT
    return value


def _check_rate_limit() -> None:
    """
    Sliding-window limiter: raises HTTPException(429) once more than
    `_rate_limit_max_requests()` requests have hit this endpoint within
    the last `_rate_limit_window_seconds()` seconds. Not thread-safe by
    design вЂ” this process serves the endpoint from a single asyncio
    event loop (uvicorn's default worker model here), so a plain
    deque is sufficient; do not reuse this helper if the deployment
    model ever moves to multiple worker processes/threads.
    """
    now = time.monotonic()
    window_start = now - _rate_limit_window_seconds()
    while _rate_limit_timestamps and _rate_limit_timestamps[0] < window_start:
        _rate_limit_timestamps.popleft()
    if len(_rate_limit_timestamps) >= _rate_limit_max_requests():
        raise HTTPException(status_code=429, detail="Too many requests")
    _rate_limit_timestamps.append(now)


def _db() -> "idb.sqlite3.Connection":  # type: ignore[name-defined]
    return idb.open_db(_DB_PATH)


def _verify_signature(raw_body: bytes, signature_header: str | None) -> None:
    """
    Verify X-Hub-Signature-256 using GITHUB_WEBHOOK_SECRET.

    Raises HTTPException(401) on any mismatch or missing header/secret.
    This check happens BEFORE the payload is parsed at all вЂ” an
    unverified request never reaches event-dispatch logic.
    """
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET is not configured")
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or malformed signature header")

    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="Signature mismatch")


async def trigger_scan_for_installation(installation_id: int, repo_full_name: str) -> None:
    """
    Clone one repo using a fresh Installation Access Token and run the
    existing scan -> fix-gen -> verify -> PR pipeline against it.

    Runs as a FastAPI background task вЂ” must not raise past its own
    boundary (errors are logged, not propagated, since there is no HTTP
    response left to attach them to by the time this runs).
    """
    owner, repo = repo_full_name.split("/", 1)
    conn = _db()
    try:
        row = conn.execute(
            "SELECT account_login FROM installations WHERE id = ?", (installation_id,)
        ).fetchone()
        account_login = row["account_login"] if row else owner
        if not idb.is_entitled(conn, account_login):
            logger.info(
                "[webhook] skipping scan for %s вЂ” no active Marketplace purchase on file",
                repo_full_name,
            )
            return
    finally:
        conn.close()

    try:
        token, _expires_at = await exchange_for_installation_token(installation_id)
    except GitHubAppAuthError:
        logger.exception("[webhook] failed to mint installation token for %s", repo_full_name)
        return
    # BACKLOG 19: register the minted token the moment it exists, so any
    # log/exception text that somehow captures it is redacted by value.
    register_runtime_credential(token)

    tmp_dir = Path(tempfile.mkdtemp(prefix="patchward-webhook-"))
    try:
        # BACKLOG 19: tokenless URL + ephemeral credential helper. The
        # token reaches git only via the subprocess environment вЂ” it is
        # never in the URL (so `git clone` cannot persist it into the
        # clone's .git/config, where the scanners and triage/fix-gen
        # subagents could read it) and never in argv (so exception text
        # that embeds argv cannot leak it).
        clone_url = tokenless_clone_url(owner, repo)
        proc = await asyncio.to_thread(
            subprocess.run,
            [
                "git",
                *credential_helper_args(),
                "clone", "--depth", "1", clone_url, str(tmp_dir / repo),
            ],
            capture_output=True,
            text=True,
            env=credential_env(token),
        )
        if proc.returncode != 0:
            # scrub_text: modern git redacts credentials from its own
            # stderr, but that is version-dependent and not guaranteed
            # (e.g. verbose/trace modes) вЂ” scrub regardless.
            logger.error(
                "[webhook] clone failed for %s: %s",
                repo_full_name,
                scrub_text(proc.stderr),
            )
            return

        proxy = CredentialProxy().load()
        anthropic_key = proxy.get_client_credentials().get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            logger.error("[webhook] ANTHROPIC_API_KEY not set вЂ” cannot run pipeline")
            return

        cfg = PatchwardConfig(
            repo_path=tmp_dir / repo,
            fix_gen=FixGenConfig(),
            verifier=VerifierConfig(),
            github=GithubConfig(owner=owner, repo=repo),
            batch=BatchConfig(),
            models=ModelsConfig(),
        )
        repo_cfg = RepoConfig(path=tmp_dir / repo, owner=owner, repo=repo)
        semaphore = asyncio.Semaphore(1)
        run_log = RunLog()

        result = await run_repo_pipeline(
            repo=repo_cfg,
            cfg=cfg,
            semaphore=semaphore,
            api_key=anthropic_key,
            github_token=token,
            run_log=run_log,
        )
        logger.info("[webhook] scan finished for %s: %s", repo_full_name, result)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    content_length: str | None = Header(default=None),
) -> dict:
    _check_body_size(content_length)

    raw_body = await request.body()
    if len(raw_body) > _max_body_bytes():
        # Defense in depth for a missing/lying Content-Length header
        # (e.g. chunked transfer-encoding) вЂ” see _check_body_size's
        # docstring for the residual-risk note on this path.
        raise HTTPException(status_code=413, detail="Payload too large")
    _verify_signature(raw_body, x_hub_signature_256)
    # Rate limiting runs AFTER signature verification so only HMAC-valid,
    # genuinely-from-GitHub requests count toward the window (see the
    # limiter's rationale comment above). A request that fails HMAC has
    # already returned 401 from _verify_signature and never reaches this
    # line, so it cannot touch or mutate the rate-limit deque.
    _check_rate_limit()
    payload = await request.json()

    event = x_github_event or "unknown"
    action = payload.get("action")
    delivery_id = x_github_delivery or ""
    logger.info(
        "[webhook] received event=%s action=%s delivery=%s", event, action, delivery_id
    )

    if event == "ping":
        return {"status": "pong"}

    if event == "installation":
        installation = payload["installation"]
        installation_id = installation["id"]
        account = installation["account"]
        conn = _db()
        try:
            if action in ("created", "unsuspend"):
                idb.upsert_installation(
                    conn, installation_id, account["login"], account["type"]
                )
                for repo in payload.get("repositories", []):
                    idb.add_installation_repo(conn, installation_id, repo["full_name"])
            elif action == "deleted":
                idb.delete_installation(conn, installation_id)
            elif action == "suspend":
                idb.mark_installation_suspended(conn, installation_id)
        finally:
            conn.close()
        return {"status": "ok"}

    if event == "installation_repositories":
        installation_id = payload["installation"]["id"]
        conn = _db()
        try:
            for repo in payload.get("repositories_added", []):
                idb.add_installation_repo(conn, installation_id, repo["full_name"])
            for repo in payload.get("repositories_removed", []):
                idb.remove_installation_repo(conn, installation_id, repo["full_name"])
        finally:
            conn.close()
        return {"status": "ok"}

    if event == "marketplace_purchase":
        mp = payload["marketplace_purchase"]
        account = payload["account"] if "account" in payload else mp["account"]
        idb_conn = _db()
        try:
            idb.upsert_marketplace_purchase(
                idb_conn,
                account_login=account["login"],
                plan_id=mp["plan"]["id"],
                unit_count=mp.get("unit_count", 1),
                billing_cycle=mp.get("billing_cycle"),
                status=action or "purchased",
            )
        finally:
            idb_conn.close()
        return {"status": "ok"}

    if event == "push":
        installation_id = payload.get("installation", {}).get("id")
        repo_full_name = payload.get("repository", {}).get("full_name")
        if installation_id and repo_full_name:
            background_tasks.add_task(
                trigger_scan_for_installation, installation_id, repo_full_name
            )
        return {"status": "scan_queued"}

    # Unrecognized event types are acknowledged, not rejected вЂ” GitHub
    # disables a webhook after enough consecutive non-2xx responses,
    # and new event types may arrive that this v0 simply doesn't act on.
    return {"status": "ignored", "event": event}


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
