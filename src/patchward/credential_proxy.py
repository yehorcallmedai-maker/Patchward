# KS-TRACE: C-P2-04, AC-P2-05
# | assumption: load_dotenv() in config.py has already run before CredentialProxy.load();
# |             _CREDENTIAL_KEYS here is the single source of truth — imported by docker_sandbox.py
# | test: test_credential_proxy.py
"""
Credential proxy for Phase 2 sandbox isolation.

All three credential keys are defined ONCE here and imported by docker_sandbox.py.
This eliminates the risk of the two lists diverging.

Trust invariants enforced here:
  C-P2-04  Credentials (ANTHROPIC_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
           MUST NOT be present in the Docker container environment.

Usage::

    proxy = CredentialProxy().load()

    # Pass to Anthropic SDK client:
    client = anthropic.Anthropic(**proxy.get_client_credentials())

    # Build container env (credentials excluded):
    container_env = proxy.get_container_env()
    proxy.assert_credentials_excluded(container_env)  # belt-and-suspenders

    # Scrub any credential values from output text:
    safe_message = proxy.scrub(finding_message)
"""
from __future__ import annotations

import os
import re

# ---------------------------------------------------------------------------
# Single source of truth for credential key names.
# docker_sandbox.py imports this — do NOT redefine there.
# KS-TRACE: C-P2-04, AC-P2-05
# ---------------------------------------------------------------------------
_CREDENTIAL_KEYS: frozenset[str] = frozenset({
    "ANTHROPIC_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "GITHUB_TOKEN",   # KS-TRACE: AC-P5-01, C-P5-03 | Phase 5 push credential
})


# ---------------------------------------------------------------------------
# BACKLOG 19 — log/exception redaction for runtime-minted credentials.
#
# CredentialProxy.scrub() is value-based over env-loaded credentials, which
# structurally cannot cover the webhook path's GitHub App Installation
# Access Tokens: those are minted per-run at runtime (never present in
# os.environ — the Fly deployment has no GITHUB_TOKEN secret at all), so
# there is no loaded value to match. Two additional layers close that gap:
#
#   1. register_runtime_credential(): the mint site registers the exact
#      token value the moment it exists, so scrub_text() can redact it
#      by value.
#   2. A pattern pass for GitHub-shaped tokens (ghp_/gho_/ghu_/ghs_/ghr_
#      prefixes and fine-grained github_pat_), catching token-shaped
#      strings nobody registered, from any source (defense in depth).
#
# scrub_text() is the shared scrubber for text bound for logs, CLI
# output, or exception messages. It deliberately does NOT replace
# CredentialProxy.scrub(), whose semantics (env-credential values in
# scanner finding messages) are unchanged.
# KS-TRACE: C-P5-03 | test: test_git_credentials.py
# ---------------------------------------------------------------------------

_RUNTIME_CREDENTIALS: set[str] = set()

# GitHub token formats: classic/app prefixes with a base62 tail (real
# tokens are 36+ chars after the prefix; 16 floor avoids redacting short
# prose lookalikes while still catching truncated real tokens), and
# fine-grained PATs (github_pat_, base62 + underscores, much longer).
_GITHUB_TOKEN_RE = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,255}\b"
    r"|\bgithub_pat_[A-Za-z0-9_]{22,255}\b"
)


def register_runtime_credential(value: str) -> None:
    """
    Register a runtime-minted secret (e.g. a GitHub App Installation
    Access Token) so scrub_text() redacts it by exact value.

    Call at the mint site, the moment the secret exists. Empty /
    whitespace-only values are ignored. The registry is process-global
    and append-only for the process lifetime; tokens expire server-side
    (installation tokens: ~1 hour), so entries going stale is harmless —
    they only ever cause redaction, never exposure.
    """
    v = (value or "").strip()
    if v:
        _RUNTIME_CREDENTIALS.add(v)


def scrub_text(text: str) -> str:
    """
    Redact credentials from text bound for logs, CLI output, or
    exception messages.

    Layer 1: exact-value replacement of every registered runtime
    credential. Layer 2: pattern-based redaction of GitHub-shaped
    tokens. Returns the input unchanged when there is nothing to redact.
    """
    if not text:
        return text
    for val in _RUNTIME_CREDENTIALS:
        if val in text:
            text = text.replace(val, "[REDACTED]")
    return _GITHUB_TOKEN_RE.sub("[REDACTED-GITHUB-TOKEN]", text)


class CredentialLeakError(RuntimeError):
    """
    Raised by assert_credentials_excluded() when a credential key is found
    in an environment dict that is about to be passed to a container.

    Attribute `key` holds the offending key name.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            f"Credential key '{key}' found in container environment — "
            "C-P2-04 violation. Credentials must never enter the container boundary."
        )


class CredentialProxy:
    """
    Loads credential values from the process environment and provides
    safe accessors that enforce the container isolation boundary.

    Credentials are stored in memory only; never logged, printed, or
    included in SARIF output.

    # KS-TRACE: C-P2-04, AC-P2-05
    """

    def __init__(self) -> None:
        # Credential values keyed by name. Populated by load().
        self._creds: dict[str, str] = {}

    def load(self) -> "CredentialProxy":
        """
        Read credential values from os.environ into self._creds.
        Keys not present in the environment are silently skipped.
        Empty-string values are skipped (not considered set).

        Returns self for chaining: CredentialProxy().load()
        """
        for key in _CREDENTIAL_KEYS:
            val = os.environ.get(key, "").strip()
            if val:
                self._creds[key] = val
        return self

    def get_client_credentials(self) -> dict[str, str]:
        """
        Return the subset of loaded credentials needed to instantiate
        the Anthropic SDK client (ANTHROPIC_API_KEY only).

        Returns empty dict if ANTHROPIC_API_KEY was not in the environment.
        """
        result: dict[str, str] = {}
        if "ANTHROPIC_API_KEY" in self._creds:
            result["ANTHROPIC_API_KEY"] = self._creds["ANTHROPIC_API_KEY"]
        return result

    def get_container_env(self) -> dict[str, str]:
        """
        Return a copy of os.environ with all _CREDENTIAL_KEYS removed.
        This is the safe environment dict to pass to Docker containers.

        # KS-TRACE: C-P2-04
        """
        return {k: v for k, v in os.environ.items() if k not in _CREDENTIAL_KEYS}

    def assert_credentials_excluded(self, env_dict: dict[str, str]) -> None:
        """
        Hard assertion: raise CredentialLeakError if ANY key in _CREDENTIAL_KEYS
        is present in env_dict. Call this before every docker run.

        This is a belt-and-suspenders check on top of the structural exclusion
        in docker_sandbox.py._build_docker_cmd(). Belt-and-suspenders because
        a future caller might accidentally pass os.environ directly.

        Args:
            env_dict: The environment dict about to be forwarded to a container.

        Raises:
            CredentialLeakError: On first credential key found in env_dict.

        # KS-TRACE: C-P2-04, AC-P2-05
        """
        for key in _CREDENTIAL_KEYS:
            if key in env_dict:
                raise CredentialLeakError(key)

    def scrub(self, text: str) -> str:
        """
        Replace every loaded credential VALUE with '[REDACTED]' in text.

        Use this before including any text in logs, SARIF messages, or CLI output
        when the source may have captured a credential value.

        Args:
            text: Raw text that may contain credential values.

        Returns:
            Text with all known credential values replaced by '[REDACTED]'.

        # KS-TRACE: C-P2-04
        """
        for val in self._creds.values():
            if val in text:
                text = text.replace(val, "[REDACTED]")
        return text
