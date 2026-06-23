# KS-TRACE: C-P2-05, C-P2-08, AC-P2-06, C-P3-10
# | assumption: cleanup idempotency covers all exit paths; KeyboardInterrupt test
# |             is the adversarial case — finally block must fire even on interrupt
# | test: this file
"""
git worktree isolation tests — KS-P2-06.

Test categories:
  0. Shared primitives — identity test (C-P3-10: no drift between worktree and worktree_common)
  1. require_git_version() — fail-fast unit tests
  2. create_worktree() — branch name and path assertions (subprocess mocked)
  3. cleanup_worktree() — idempotency (no raise on missing worktree/branch)
  4. worktree_context() — finally-block invariant under clean exit, exception,
     KeyboardInterrupt; path routing invariant
  5. Working branch invariant — no git checkout issued on original repo

Note on patch targets: require_git_version, git_worktree_add, and git_worktree_remove
live in repomend.worktree_common (single source of truth per C-P3-10). Tests that
mock subprocess.run for those operations patch "repomend.worktree_common.subprocess.run".
Tests that mock the create_worktree/cleanup_worktree function objects directly patch
"repomend.worktree.create_worktree" / "repomend.worktree.cleanup_worktree" — unchanged.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import repomend.worktree as worktree_mod
import repomend.worktree_common as worktree_common_mod
from repomend.worktree import (
    GitVersionError,
    _worktree_path,
    cleanup_worktree,
    create_worktree,
    require_git_version,
    worktree_context,
)


# ---------------------------------------------------------------------------
# 0. Shared primitives — identity test
# ---------------------------------------------------------------------------

def test_shared_primitives_single_source() -> None:
    """
    C-P3-10: require_git_version and GitVersionError must be the identical
    objects in worktree and worktree_common — imported, not copy-pasted.
    Same pattern as test_credential_keys_single_source_of_truth in Phase 2.
    """
    assert worktree_mod.require_git_version is worktree_common_mod.require_git_version, (
        "require_git_version must be the same object in worktree and worktree_common — C-P3-10"
    )
    assert worktree_mod.GitVersionError is worktree_common_mod.GitVersionError, (
        "GitVersionError must be the same object in worktree and worktree_common — C-P3-10"
    )


# ---------------------------------------------------------------------------
# 1. require_git_version() — fail-fast
# ---------------------------------------------------------------------------

def test_require_git_version_passes() -> None:
    """Mock git --version returning 2.39.0; assert no exception."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "git version 2.39.0\n"
    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        require_git_version()  # must not raise


def test_require_git_version_passes_windows_format() -> None:
    """Windows git appends '.windows.N' — parser must still extract major.minor."""
    mock_result = MagicMock()
    mock_result.stdout = "git version 2.42.0.windows.2\n"
    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        require_git_version()  # must not raise


def test_require_git_version_fails() -> None:
    """Mock git --version returning 2.4.0; assert GitVersionError with version in message."""
    mock_result = MagicMock()
    mock_result.stdout = "git version 2.4.0\n"
    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        with pytest.raises(GitVersionError) as exc_info:
            require_git_version()
    assert "2.4" in str(exc_info.value)
    assert "2.5+" in str(exc_info.value)


def test_require_git_version_fails_on_exact_boundary() -> None:
    """git 2.4.99 is still below 2.5 — must raise."""
    mock_result = MagicMock()
    mock_result.stdout = "git version 2.4.99\n"
    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        with pytest.raises(GitVersionError):
            require_git_version()


def test_require_git_version_not_found() -> None:
    """git not on PATH → FileNotFoundError → GitVersionError with actionable message."""
    with patch(
        "repomend.worktree_common.subprocess.run",
        side_effect=FileNotFoundError("git not found"),
    ):
        with pytest.raises(GitVersionError) as exc_info:
            require_git_version()
    assert "PATH" in str(exc_info.value) or "git" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 2. create_worktree() — branch name and path assertions
# ---------------------------------------------------------------------------

def test_create_worktree_creates_branch() -> None:
    """create_worktree() calls git worktree add with correct branch name."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result) as mock_run:
        scan_path = create_worktree(Path("/repo"), "abc12345")

    mock_run.assert_called_once()
    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "git"
    assert cmd[1] == "worktree"
    assert cmd[2] == "add"
    # Branch name must follow repomend/scan-{scan_id} convention
    assert "repomend/scan-abc12345" in cmd


def test_create_worktree_returns_deterministic_path() -> None:
    """create_worktree() returns the same path as _worktree_path() for the same scan_id."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        returned = create_worktree(Path("/repo"), "abc12345")

    expected = _worktree_path("abc12345")
    assert returned == expected


def test_worktree_path_contains_scan_id() -> None:
    """_worktree_path() embeds the scan_id in the directory name."""
    path = _worktree_path("deadbeef")
    assert "deadbeef" in str(path)
    assert "repomend-scan" in str(path)


# ---------------------------------------------------------------------------
# 3. cleanup_worktree() — idempotency
# ---------------------------------------------------------------------------

def test_cleanup_is_idempotent() -> None:
    """
    cleanup_worktree() called twice must not raise on the second call.
    Simulates: cleanup after scan completes, then cleanup called again
    (e.g. by a double-finally edge case or manual cleanup).
    """
    mock_result = MagicMock()
    mock_result.returncode = 128  # git "not found" error — worktree/branch already gone

    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        cleanup_worktree(Path("/repo"), "abc12345")  # first call
        cleanup_worktree(Path("/repo"), "abc12345")  # second call — must not raise


def test_cleanup_does_not_raise_when_worktree_missing() -> None:
    """cleanup_worktree() must not raise if worktree was never created."""
    mock_result = MagicMock()
    mock_result.returncode = 128  # fatal: not a git repository / no such path

    with patch("repomend.worktree_common.subprocess.run", return_value=mock_result):
        cleanup_worktree(Path("/repo"), "nonexistent-id")  # must not raise


def test_cleanup_runs_both_steps_even_if_first_fails() -> None:
    """
    cleanup_worktree() must run git branch -D even if git worktree remove fails.
    Both cleanup steps are independent — one failing must not skip the other.
    """
    call_log: list[list[str]] = []

    def record_calls(cmd, **kwargs):
        call_log.append(list(cmd))
        result = MagicMock()
        result.returncode = 128 if "remove" in cmd else 0
        return result

    with patch("repomend.worktree_common.subprocess.run", side_effect=record_calls):
        cleanup_worktree(Path("/repo"), "abc12345")

    cmds = [" ".join(c) for c in call_log]
    assert any("worktree remove" in c for c in cmds), "git worktree remove not called"
    assert any("branch -D" in c for c in cmds), "git branch -D not called"


# ---------------------------------------------------------------------------
# 4. worktree_context() — finally-block invariant
# ---------------------------------------------------------------------------

def test_worktree_context_yields_scan_path(tmp_path: Path) -> None:
    """worktree_context() yields the path returned by create_worktree."""
    fake_worktree = tmp_path / "repomend-scan-abc123"
    fake_worktree.mkdir()

    with patch("repomend.worktree.create_worktree", return_value=fake_worktree):
        with patch("repomend.worktree.cleanup_worktree"):
            with worktree_context(tmp_path) as scan_path:
                assert scan_path == fake_worktree


def test_cleanup_runs_on_clean_exit(tmp_path: Path) -> None:
    """cleanup_worktree() must be called when worktree_context exits cleanly."""
    with patch("repomend.worktree.create_worktree", return_value=tmp_path / "wt"):
        with patch("repomend.worktree.cleanup_worktree") as mock_cleanup:
            with worktree_context(tmp_path):
                pass  # clean exit
    mock_cleanup.assert_called_once()


def test_cleanup_runs_on_exception(tmp_path: Path) -> None:
    """
    cleanup_worktree() must be called even when an exception is raised
    inside the worktree_context block (e.g. scanner crash, hook denial).
    AC-P2-06: No leaked repomend/scan-* branch regardless of exit path.
    """
    with patch("repomend.worktree.create_worktree", return_value=tmp_path / "wt"):
        with patch("repomend.worktree.cleanup_worktree") as mock_cleanup:
            with pytest.raises(RuntimeError, match="scanner crash"):
                with worktree_context(tmp_path):
                    raise RuntimeError("scanner crash")
    mock_cleanup.assert_called_once()


def test_cleanup_runs_on_keyboard_interrupt(tmp_path: Path) -> None:
    """
    cleanup_worktree() must be called on KeyboardInterrupt.
    Adversarial case: user hits Ctrl-C mid-scan — worktree must still be removed.
    AC-P2-06 invariant: no leaked branch under any exit path.
    """
    with patch("repomend.worktree.create_worktree", return_value=tmp_path / "wt"):
        with patch("repomend.worktree.cleanup_worktree") as mock_cleanup:
            with pytest.raises(KeyboardInterrupt):
                with worktree_context(tmp_path):
                    raise KeyboardInterrupt()
    mock_cleanup.assert_called_once()


def test_cleanup_runs_on_system_exit(tmp_path: Path) -> None:
    """cleanup_worktree() must be called on SystemExit (e.g. typer.Exit from hook)."""
    with patch("repomend.worktree.create_worktree", return_value=tmp_path / "wt"):
        with patch("repomend.worktree.cleanup_worktree") as mock_cleanup:
            with pytest.raises(SystemExit):
                with worktree_context(tmp_path):
                    raise SystemExit(1)
    mock_cleanup.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Working branch invariant and path routing
# ---------------------------------------------------------------------------

def test_scanner_receives_worktree_path_not_original(tmp_path: Path) -> None:
    """
    C-P2-08: worktree_context yields a path that is NOT the original repo_path.
    Scanners receive scan_path from the context — not the caller's repo.
    """
    original_path = tmp_path / "my-repo"
    original_path.mkdir()
    fake_worktree = tmp_path / "repomend-scan-deadbeef"
    fake_worktree.mkdir()

    with patch("repomend.worktree.create_worktree", return_value=fake_worktree):
        with patch("repomend.worktree.cleanup_worktree"):
            with worktree_context(original_path) as scan_path:
                # Scanner receives scan_path, not original_path
                assert scan_path == fake_worktree
                assert scan_path != original_path, (
                    "Scanner must receive worktree path, not original repo_path — C-P2-08"
                )


def test_working_branch_unchanged(tmp_path: Path) -> None:
    """
    C-P2-08: worktree_context must not issue git checkout or git switch on the
    original repo. The caller's working branch is never touched.
    """
    git_commands_issued: list[list[str]] = []

    def record_and_succeed(cmd, **kwargs):
        git_commands_issued.append(list(cmd))
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        return result

    with patch("repomend.worktree_common.subprocess.run", side_effect=record_and_succeed):
        with worktree_context(tmp_path):
            pass

    # No git checkout or git switch must be issued — that would change the working branch
    for cmd in git_commands_issued:
        cmd_str = " ".join(cmd)
        assert "checkout" not in cmd_str, (
            f"git checkout issued — would change working branch: {cmd_str}"
        )
        assert "switch" not in cmd_str, (
            f"git switch issued — would change working branch: {cmd_str}"
        )


def test_scan_id_is_unique_across_contexts(tmp_path: Path) -> None:
    """Each worktree_context call generates a unique scan_id (uuid4 short)."""
    scan_ids: list[str] = []

    def capture_create(repo_path: Path, scan_id: str) -> Path:
        scan_ids.append(scan_id)
        wt = tmp_path / f"wt-{scan_id}"
        wt.mkdir(exist_ok=True)
        return wt

    with patch("repomend.worktree.create_worktree", side_effect=capture_create):
        with patch("repomend.worktree.cleanup_worktree"):
            with worktree_context(tmp_path):
                pass
            with worktree_context(tmp_path):
                pass

    assert len(scan_ids) == 2
    assert scan_ids[0] != scan_ids[1], "Each context must use a unique scan_id"
    assert len(scan_ids[0]) == 8, "scan_id must be 8 hex characters (uuid4.hex[:8])"
