# KS-TRACE: BACKLOG 19 | C-P5-03 (token must never appear in logs/disk/argv)
# | test: test_git_credentials.py
"""
Ephemeral git credential passing — BACKLOG 19.

Git subprocesses (clone on the webhook path, push on both paths) used to
authenticate via a token embedded in the remote URL
(``https://x-access-token:<token>@github.com/...``). That form leaks the
token in two independent ways, both empirically confirmed in the
BACKLOG 19 scoping pass (2026-07-27):

1. ``git clone`` persists the full credential-bearing URL into the
   clone's ``.git/config`` (remote.origin.url) for the life of the
   checkout. On the webhook path the cloned repo — including ``.git/`` —
   is exactly the tree the scanners and the triage/fix-gen subagents
   read (ADR-013 treats that content as adversarial), so the live token
   sat inside the untrusted boundary on every run.
2. A token-bearing URL in the subprocess argv is embedded verbatim by
   ``str(subprocess.TimeoutExpired)`` (Python formats the full command
   into the message — no git-side credential redaction applies), which
   then flowed into logs and CLI output via generic exception handlers.

This module supplies the replacement mechanism: a **tokenless remote
URL** plus an **inline git credential helper** that reads the token from
a process-scoped environment variable at auth time. The token is
therefore never part of the URL (nothing to persist into
``.git/config``), never part of the argv (nothing for exception text to
embed), and never written to disk at any point.

The helper is a ``!``-prefixed shell fragment; git runs it under its own
``sh`` (git-for-windows bundles one), so the mechanism is portable
across the CLI path (Windows) and the webhook path (Linux). The leading
empty ``credential.helper=`` clears any system-configured helpers (e.g.
an OS credential store) so ours is the only one consulted — the token
must not be forwarded to, or stored by, any other helper.
"""
from __future__ import annotations

import os

# Environment variable the helper reads the token from. Set only on the
# git subprocess's own environment via credential_env(); never exported
# to the parent process.
GIT_TOKEN_ENV = "PATCHWARD_GIT_TOKEN"

# Inline credential helper. Executed by git's own sh; echoes the
# username git expects for GitHub App installation tokens / PATs over
# HTTPS, and the token from the subprocess environment. Contains no
# secret itself, so it is safe in argv.
_HELPER = (
    '!f() { echo "username=x-access-token"; '
    'echo "password=$' + GIT_TOKEN_ENV + '"; }; f'
)


def tokenless_clone_url(owner: str, repo: str) -> str:
    """
    Build the plain HTTPS remote URL with NO credential component.

    Replaces ``clone_url_with_token()`` (removed in BACKLOG 19), whose
    docstring claimed git does not persist the URL's credential portion
    into ``.git/config`` — that claim was false (empirically falsified
    2026-07-27: a one-shot ``git clone`` of a userinfo-bearing URL
    writes it verbatim to remote.origin.url).
    """
    return f"https://github.com/{owner}/{repo}.git"


def credential_helper_args() -> list[str]:
    """
    Git argv fragment enabling the ephemeral helper.

    Must be placed between ``git`` and the subcommand, e.g.::

        ["git", *credential_helper_args(), "clone", url, dest]

    The first ``-c credential.helper=`` (empty value) resets the helper
    list so no system/global helper is consulted or fed the credential;
    the second installs the inline env-reading helper. ``-c`` settings
    are per-invocation only — unlike ``git clone --config``, nothing
    here is persisted into the resulting clone's ``.git/config``.
    """
    return [
        "-c", "credential.helper=",
        "-c", f"credential.helper={_HELPER}",
    ]


def credential_env(token: str) -> dict[str, str]:
    """
    Environment dict for the git subprocess: the parent environment
    (unchanged from prior behavior — git already inherited it) plus the
    token under GIT_TOKEN_ENV for the helper to read.

    The returned dict is a copy; os.environ itself is never mutated.
    """
    env = dict(os.environ)
    env[GIT_TOKEN_ENV] = token
    return env
