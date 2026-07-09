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


def test_healthz() -> None:
    client = TestClient(webhook.app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
