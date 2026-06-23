# KS-TRACE: C-P2-04, AC-P2-05
# | assumption: load_dotenv() has already populated os.environ before load() is called;
# |             monkeypatch provides the same isolation in tests
# | test: this file
"""
CredentialProxy tests — KS-P2-05.

Test categories:
  1. get_container_env(): credential keys excluded, safe vars preserved
  2. assert_credentials_excluded(): raises on leak, passes on clean dict
  3. get_client_credentials(): returns ANTHROPIC_API_KEY when set, empty when not
  4. scrub(): replaces loaded credential values with [REDACTED]
  5. Single source of truth: docker_sandbox._CREDENTIAL_KEYS imported from credential_proxy
  6. Call-sequence invariant: assert before docker run pattern
"""
from __future__ import annotations

import os

import pytest

from repomend.credential_proxy import (
    _CREDENTIAL_KEYS,
    CredentialLeakError,
    CredentialProxy,
)


# ---------------------------------------------------------------------------
# 1. get_container_env() — credential keys excluded, safe vars preserved
# ---------------------------------------------------------------------------

def test_credentials_excluded_from_container_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-P2-05: get_container_env() must not contain any credential key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    proxy = CredentialProxy()
    env = proxy.get_container_env()
    for key in _CREDENTIAL_KEYS:
        assert key not in env, f"Credential key '{key}' found in container env — C-P2-04 violation"


def test_container_env_preserves_non_credential_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_container_env() must preserve non-credential env vars (PATH, etc.)."""
    monkeypatch.setenv("SAFE_VAR", "allowed_value")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    proxy = CredentialProxy()
    env = proxy.get_container_env()
    assert "SAFE_VAR" in env
    assert env["SAFE_VAR"] == "allowed_value"
    assert "ANTHROPIC_API_KEY" not in env


# ---------------------------------------------------------------------------
# 2. assert_credentials_excluded() — hard block on credential leak
# ---------------------------------------------------------------------------

def test_assert_raises_on_leak() -> None:
    """assert_credentials_excluded() raises CredentialLeakError when a credential key present."""
    proxy = CredentialProxy()
    bad_env = {"ANTHROPIC_API_KEY": "sk-ant-leaked", "SAFE_VAR": "ok"}
    with pytest.raises(CredentialLeakError) as exc_info:
        proxy.assert_credentials_excluded(bad_env)
    assert "ANTHROPIC_API_KEY" in str(exc_info.value)
    assert exc_info.value.key == "ANTHROPIC_API_KEY"


@pytest.mark.parametrize("credential_key", sorted(_CREDENTIAL_KEYS))
def test_assert_raises_on_each_credential_key(credential_key: str) -> None:
    """assert_credentials_excluded() catches every key in _CREDENTIAL_KEYS."""
    proxy = CredentialProxy()
    with pytest.raises(CredentialLeakError) as exc_info:
        proxy.assert_credentials_excluded({credential_key: "leaked-value"})
    assert exc_info.value.key == credential_key


def test_assert_passes_on_clean_env() -> None:
    """assert_credentials_excluded() must not raise when no credential keys present."""
    proxy = CredentialProxy()
    clean_env = {"SAFE_VAR": "ok", "PATH": "/usr/bin:/usr/local/bin"}
    proxy.assert_credentials_excluded(clean_env)  # must not raise


def test_assert_passes_on_empty_dict() -> None:
    """assert_credentials_excluded({}) must not raise."""
    CredentialProxy().assert_credentials_excluded({})


# ---------------------------------------------------------------------------
# 3. get_client_credentials() — ANTHROPIC_API_KEY for SDK client
# ---------------------------------------------------------------------------

def test_client_credentials_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client_credentials() returns ANTHROPIC_API_KEY when set in environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-123")
    proxy = CredentialProxy().load()
    creds = proxy.get_client_credentials()
    assert "ANTHROPIC_API_KEY" in creds
    assert creds["ANTHROPIC_API_KEY"] == "sk-ant-test-key-123"


def test_client_credentials_absent_when_not_in_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client_credentials() returns empty dict when ANTHROPIC_API_KEY not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    proxy = CredentialProxy().load()
    creds = proxy.get_client_credentials()
    assert creds == {}


def test_client_credentials_does_not_include_langfuse_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client_credentials() returns ONLY ANTHROPIC_API_KEY, not Langfuse keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    proxy = CredentialProxy().load()
    creds = proxy.get_client_credentials()
    assert "LANGFUSE_PUBLIC_KEY" not in creds
    assert "LANGFUSE_SECRET_KEY" not in creds


def test_load_skips_empty_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """load() must not add a key if the env var is set but empty."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    proxy = CredentialProxy().load()
    assert "ANTHROPIC_API_KEY" not in proxy._creds


# ---------------------------------------------------------------------------
# 4. scrub() — replace credential values with [REDACTED]
# ---------------------------------------------------------------------------

def test_no_credential_in_sarif_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    scrub() replaces loaded credential values in SARIF message text.
    Covers the adversarial case from Phase 2 INTAKE §4:
    fixture file contains 'ANTHROPIC_API_KEY=sk-ant-fake'.
    """
    fake_key = "sk-ant-xxxxxxxxxxxxxxxxxx"
    monkeypatch.setenv("ANTHROPIC_API_KEY", fake_key)
    proxy = CredentialProxy().load()
    raw_message = f"ANTHROPIC_API_KEY={fake_key}"
    scrubbed = proxy.scrub(raw_message)
    assert fake_key not in scrubbed
    assert "[REDACTED]" in scrubbed


def test_scrub_returns_unchanged_when_no_credentials_loaded() -> None:
    """scrub() on a proxy with no credentials loaded returns text unchanged."""
    proxy = CredentialProxy()  # no .load()
    text = "some finding message with no credential values"
    assert proxy.scrub(text) == text


def test_scrub_handles_multiple_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """scrub() replaces all loaded credential values, not just the first."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-abc")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-xyz")
    proxy = CredentialProxy().load()
    text = "api=sk-ant-abc lf=sk-lf-xyz"
    scrubbed = proxy.scrub(text)
    assert "sk-ant-abc" not in scrubbed
    assert "sk-lf-xyz" not in scrubbed
    assert scrubbed.count("[REDACTED]") == 2


def test_scrub_leaves_clean_text_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """scrub() must not alter text that doesn't contain any credential value."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    proxy = CredentialProxy().load()
    clean_text = "subprocess.run(shell=True) at line 24 in vulnerable.py"
    assert proxy.scrub(clean_text) == clean_text


# ---------------------------------------------------------------------------
# 5. Single source of truth: docker_sandbox._CREDENTIAL_KEYS imported from here
# ---------------------------------------------------------------------------

def test_credential_keys_single_source_of_truth() -> None:
    """
    docker_sandbox._CREDENTIAL_KEYS must be the same object imported from
    credential_proxy — not a separate definition that could diverge.
    """
    from repomend.docker_sandbox import _CREDENTIAL_KEYS as sandbox_keys
    from repomend.credential_proxy import _CREDENTIAL_KEYS as proxy_keys
    assert sandbox_keys is proxy_keys, (
        "_CREDENTIAL_KEYS in docker_sandbox.py must be imported from credential_proxy.py, "
        "not redefined. Two separate frozensets can diverge."
    )


def test_credential_keys_contains_all_three() -> None:
    """_CREDENTIAL_KEYS must cover all three credential vars."""
    assert "ANTHROPIC_API_KEY" in _CREDENTIAL_KEYS
    assert "LANGFUSE_PUBLIC_KEY" in _CREDENTIAL_KEYS
    assert "LANGFUSE_SECRET_KEY" in _CREDENTIAL_KEYS


# ---------------------------------------------------------------------------
# 6. Call-sequence invariant: assert before docker run
# ---------------------------------------------------------------------------

def test_assert_called_before_docker_run() -> None:
    """
    AC-P2-05: Demonstrates the correct pre-flight sequence before any Docker run.
    get_container_env() → assert_credentials_excluded() → run_in_container().
    Verifies that a poisoned env dict is caught BEFORE Docker is invoked.
    """
    proxy = CredentialProxy()

    # Correct pattern: get_container_env() returns a clean dict, assertion passes.
    container_env = proxy.get_container_env()
    proxy.assert_credentials_excluded(container_env)  # must not raise

    # Wrong pattern: raw os.environ passed directly (simulates future developer mistake).
    # Poison it with a credential key to show the assertion catches it.
    poisoned_env: dict[str, str] = {"ANTHROPIC_API_KEY": "sk-ant-leaked", "SAFE": "ok"}
    with pytest.raises(CredentialLeakError):
        proxy.assert_credentials_excluded(poisoned_env)
        # If this raises, run_in_container() is never reached — correct behaviour.


# ---------------------------------------------------------------------------
# KS-P5-02 STEP 2 — GITHUB_TOKEN in CredentialProxy (AC-P5-01, C-P5-03)
# ---------------------------------------------------------------------------

def test_github_token_in_credential_keys() -> None:
    """GITHUB_TOKEN must be in _CREDENTIAL_KEYS single source of truth (AC-P5-01)."""
    assert "GITHUB_TOKEN" in _CREDENTIAL_KEYS, (
        "GITHUB_TOKEN must be in _CREDENTIAL_KEYS so scrub() redacts it automatically"
    )


def test_github_token_scrubbed(monkeypatch: pytest.MonkeyPatch) -> None:
    """scrub() replaces GITHUB_TOKEN value with [REDACTED] in any string (C-P5-03)."""
    fake_token = "ghp_faketoken1234567890ABCDEF"
    monkeypatch.setenv("GITHUB_TOKEN", fake_token)
    proxy = CredentialProxy().load()
    url = f"https://oauth2:{fake_token}@github.com/acme/my-app.git"
    scrubbed = proxy.scrub(url)
    assert fake_token not in scrubbed, "GITHUB_TOKEN value must be redacted"
    assert "[REDACTED]" in scrubbed


def test_github_token_single_source_of_truth() -> None:
    """_CREDENTIAL_KEYS is the single source imported by docker_sandbox (C-P2-04 pattern)."""
    from repomend.docker_sandbox import _CREDENTIAL_KEYS as sandbox_keys
    assert _CREDENTIAL_KEYS is sandbox_keys, (
        "_CREDENTIAL_KEYS must be the same object in credential_proxy and docker_sandbox"
    )
