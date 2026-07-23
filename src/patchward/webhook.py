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
  - Any payment-processing code. GitHub is merchant of record — this
    file only ever reacts to marketplace_purchase webhook events to
    keep is_entitled() current; it never calls a payments API directly.
"""
from __future__ import annotations

import asyncio
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
from pathlib import Path

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
from patchward.credential_proxy import CredentialProxy
from patchward.github_app_auth import (
    GitHubAppAuthError,
    clone_url_with_token,
    exchange_for_installation_token,
)
from patchward.pipeline import run_repo_pipeline
from patchward.run_log import RunLog

logger = logging.getLogger(__name__)

app = FastAPI(title="Patchward Webhook Receiver")

_DB_PATH = Path(os.environ.get("PATCHWARD_WEBHOOK_DB", "runs/webhook_state.db"))

# BACKLOG 5 (Phase 9 Exposure Gate) — request body size limit.
# GitHub's own hard cap on webhook payloads is 25 MB (a larger event
# simply never gets delivered — see
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
            "(must be an integer >= 1) — using default %d",
            raw,
            _DEFAULT_MAX_BODY_BYTES,
        )
        return _DEFAULT_MAX_BODY_BYTES
    return value


def _check_body_size(content_length_header: str | None) -> None:
    """
    Reject oversized deliveries by Content-Length before the body is read,
    when the client sends that header (GitHub always does). This is a
    fast-path check only — a client omitting or lying about
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


# BACKLOG 5 — rate limiting on /webhooks/github. The limiter is called
# AFTER _verify_signature in the handler (Phase 9 security-boundary
# change), so it counts only HMAC-valid, genuinely-from-GitHub requests.
# An unauthenticated flood is rejected at 401 before it ever reaches the
# limiter and therefore cannot consume the budget — that closes the
# starvation vector where anonymous traffic filling a shared window would
# push GitHub's real deliveries into 429s and, via GitHub's
# consecutive-non-2xx auto-disable, risk the webhook being turned off.
# The residual cost of an unauthenticated flood (buffering + one HMAC per
# request) is bounded by the body-size cap above and consciously accepted
# at v0 scope, not re-solved with a second pre-auth limiter (ADR-030).
# Single Fly machine, scale-to-zero (fly.toml), no shared store between
# instances by design (ADR-030) — an in-memory sliding-window counter is
# consistent with that same v0 scope, not a compromise pending a "real"
# implementation. This bounds a runaway/replay flood of otherwise-valid
# GitHub deliveries; it is not a per-installation fairness mechanism.
_RATE_LIMIT_MAX_REQUESTS_DEFAULT = 60
_RATE_LIMIT_WINDOW_SECONDS_DEFAULT = 60.0

_rate_limit_timestamps: collections.deque[float] = collections.deque()


def _rate_limit_max_requests() -> int:
    # Same guard shape as _max_body_bytes. A max < 1 (zero or negative)
    # would make _check_rate_limit reject on the very first request and
    # never accept again — a permanent-429 outage — so it falls back to
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
            "(must be an integer >= 1) — using default %d",
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
            "(must be a finite number > 0) — using default %s",
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
    design — this process serves the endpoint from a single asyncio
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
    This check happens BEFORE the payload is parsed at all — an
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

    Runs as a FastAPI background task — must not raise past its own
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
                "[webhook] skipping scan for %s — no active Marketplace purchase on file",
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

    tmp_dir = Path(tempfile.mkdtemp(prefix="patchward-webhook-"))
    try:
        clone_url = clone_url_with_token(owner, repo, token)
        proc = await asyncio.to_thread(
            subprocess.run,
            ["git", "clone", "--depth", "1", clone_url, str(tmp_dir / repo)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            logger.error("[webhook] clone failed for %s: %s", repo_full_name, proc.stderr)
            return

        proxy = CredentialProxy().load()
        anthropic_key = proxy.get_client_credentials().get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            logger.error("[webhook] ANTHROPIC_API_KEY not set — cannot run pipeline")
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
        # (e.g. chunked transfer-encoding) — see _check_body_size's
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

    # Unrecognized event types are acknowledged, not rejected — GitHub
    # disables a webhook after enough consecutive non-2xx responses,
    # and new event types may arrive that this v0 simply doesn't act on.
    return {"status": "ignored", "event": event}


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
