# KS-TRACE: P1-WEBHOOK-01 | test: JWT signing, key loading, token exchange
from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from patchward.github_app_auth import (
    GitHubAppAuthError,
    clone_url_with_token,
    exchange_for_installation_token,
    generate_app_jwt,
)


@pytest.fixture(scope="module")
def rsa_key_pem() -> bytes:
    """A throwaway 2048-bit RSA key, generated once per test module run —
    never a real credential, exists only to make pyjwt.encode/decode
    exercise real RS256 logic instead of being mocked away entirely."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_generate_app_jwt_raw_pem(monkeypatch: pytest.MonkeyPatch, rsa_key_pem: bytes) -> None:
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pem.decode("utf-8"))
    token = generate_app_jwt(app_id="4249087")
    # Decode without verifying signature just to confirm payload shape —
    # verifying would need the public key, which is beside the point here.
    payload = pyjwt.decode(token, options={"verify_signature": False})
    assert payload["iss"] == "4249087"
    assert payload["exp"] - payload["iat"] <= 600  # GitHub's 10-minute cap


def test_generate_app_jwt_base64_pem(monkeypatch: pytest.MonkeyPatch, rsa_key_pem: bytes) -> None:
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_B64", base64.b64encode(rsa_key_pem).decode("ascii"))
    token = generate_app_jwt(app_id="4249087")
    payload = pyjwt.decode(token, options={"verify_signature": False})
    assert payload["iss"] == "4249087"


def test_generate_app_jwt_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_B64", raising=False)
    with pytest.raises(GitHubAppAuthError):
        generate_app_jwt(app_id="4249087")


def test_generate_app_jwt_missing_app_id_raises(
    monkeypatch: pytest.MonkeyPatch, rsa_key_pem: bytes
) -> None:
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pem.decode("utf-8"))
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    with pytest.raises(GitHubAppAuthError):
        generate_app_jwt()


@pytest.mark.asyncio
async def test_exchange_for_installation_token_success(
    monkeypatch: pytest.MonkeyPatch, rsa_key_pem: bytes
) -> None:
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pem.decode("utf-8"))
    monkeypatch.setenv("GITHUB_APP_ID", "4249087")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "token": "ghs_faketoken123",
        "expires_at": "2026-07-09T12:00:00Z",
    }

    # Patch the whole AsyncClient, not just .post — patching only .post
    # still lets __init__ build a real transport, which fails in any
    # sandbox that routes egress through a proxy httpx can't reach.
    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        token, expires_at = await exchange_for_installation_token(145267704)

    assert token == "ghs_faketoken123"
    assert expires_at == "2026-07-09T12:00:00Z"


@pytest.mark.asyncio
async def test_exchange_for_installation_token_failure_raises(
    monkeypatch: pytest.MonkeyPatch, rsa_key_pem: bytes
) -> None:
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pem.decode("utf-8"))
    monkeypatch.setenv("GITHUB_APP_ID", "4249087")

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    with patch("httpx.AsyncClient", return_value=mock_client_cm):
        with pytest.raises(GitHubAppAuthError):
            await exchange_for_installation_token(999999)


def test_clone_url_with_token_embeds_token() -> None:
    url = clone_url_with_token("acme", "backend", "ghs_abc123")
    assert url == "https://x-access-token:ghs_abc123@github.com/acme/backend.git"
