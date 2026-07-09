# KS-TRACE: P1-WEBHOOK-01 | assumption: GITHUB_APP_ID and
# GITHUB_APP_PRIVATE_KEY (PEM, either raw or base64-encoded) are
# present in the process environment — never committed to disk
# in this repo | test: test_github_app_auth.py
"""
GitHub App authentication: JWT signing and Installation Access Token
exchange.

This is the actual trust mechanism the Marketplace build plan (P1.3 in
docs/architecture/patchward-webhook-billing-design.md) calls out as the
answer to enterprise due diligence — every scan run uses a token scoped
to exactly one installation, valid for at most one hour, generated fresh
from the App's private key rather than a long-lived PAT.

Nothing in this module touches disk for the private key. The key is read
once from an environment variable at process start (set as a platform
secret — Fly.io `fly secrets set`, Render environment group, etc. — never
as a file committed to this repo or left in a Downloads folder).
"""
from __future__ import annotations

import base64
import os
import time

import httpx
import jwt as pyjwt

_GITHUB_API = "https://api.github.com"


class GitHubAppAuthError(RuntimeError):
    """Raised when JWT signing or the token exchange fails."""


def _load_private_key() -> str:
    """
    Read the App's private key from the environment.

    Accepts either the raw PEM text (with literal newlines, which most
    platform secret stores handle fine) or a base64-encoded copy of the
    PEM (useful when a platform's secret UI mangles literal newlines).

    Raises GitHubAppAuthError if neither is set.
    """
    raw = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
    if raw:
        return raw
    encoded = os.environ.get("GITHUB_APP_PRIVATE_KEY_B64", "").strip()
    if encoded:
        return base64.b64decode(encoded).decode("utf-8")
    raise GitHubAppAuthError(
        "Neither GITHUB_APP_PRIVATE_KEY nor GITHUB_APP_PRIVATE_KEY_B64 "
        "is set — cannot sign a GitHub App JWT."
    )


def generate_app_jwt(app_id: str | None = None) -> str:
    """
    Generate a short-lived JWT signed with the App's private key.

    Per GitHub's own limit, the JWT may be valid for at most 10 minutes.
    ``iat`` is backdated by 60 seconds to tolerate clock drift between
    this process and GitHub's servers (GitHub's own recommendation).

    Args:
        app_id: GitHub App ID. Falls back to the GITHUB_APP_ID env var.

    Returns:
        Encoded JWT string, ready to use as a Bearer token against the
        GitHub App API (not the Installation API — see
        exchange_for_installation_token for that).
    """
    resolved_app_id = app_id or os.environ.get("GITHUB_APP_ID", "")
    if not resolved_app_id:
        raise GitHubAppAuthError(
            "No app_id passed and GITHUB_APP_ID is not set."
        )
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (9 * 60),  # 9 minutes — stays under GitHub's 10-minute cap
        "iss": resolved_app_id,
    }
    private_key = _load_private_key()
    return pyjwt.encode(payload, private_key, algorithm="RS256")


async def exchange_for_installation_token(
    installation_id: int,
    app_id: str | None = None,
) -> tuple[str, str]:
    """
    Exchange a freshly-generated App JWT for a 1-hour Installation
    Access Token scoped to one installation.

    Args:
        installation_id: The GitHub installation ID (from the
            `installation` webhook payload, e.g. payload["installation"]["id"]).
        app_id: GitHub App ID. Falls back to GITHUB_APP_ID env var.

    Returns:
        (token, expires_at_iso) tuple. ``token`` is used as
        ``x-access-token:<token>@github.com`` in a git clone URL, or as
        a Bearer token against the REST API for that installation only.

    Raises:
        GitHubAppAuthError: on any non-2xx response from GitHub.
    """
    app_jwt = generate_app_jwt(app_id)
    url = f"{_GITHUB_API}/app/installations/{installation_id}/access_tokens"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    if response.status_code != 201:
        raise GitHubAppAuthError(
            f"Installation token exchange failed for installation "
            f"{installation_id}: HTTP {response.status_code} {response.text}"
        )
    body = response.json()
    return body["token"], body["expires_at"]


def clone_url_with_token(owner: str, repo: str, token: str) -> str:
    """
    Build a git-clonable HTTPS URL that authenticates with an
    Installation Access Token instead of a stored credential.

    The token is embedded in the URL only for the duration of the
    clone/push subprocess call — it is never written to disk (git
    does not persist the remote URL's credential portion in
    .git/config for a one-shot clone using this form) and expires
    within an hour regardless.
    """
    return f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
