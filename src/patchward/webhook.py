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
import hashlib
import hmac
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from patchward import installations_db as idb
from patchward.config import (
    BatchConfig,
    FixGenConfig,
    GithubConfig,
    ModelsConfig,
    RepoConfig,
    RepomendConfig,
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

        cfg = RepomendConfig(
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
) -> dict:
    raw_body = await request.body()
    _verify_signature(raw_body, x_hub_signature_256)
    payload = await request.json()

    event = x_github_event or "unknown"
    action = payload.get("action")
    logger.info("[webhook] received event=%s action=%s", event, action)

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
