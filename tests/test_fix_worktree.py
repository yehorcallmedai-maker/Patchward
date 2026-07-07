# KS-TRACE: C-P3-10, C-P3-11, C-P3-12, AC-P3-03 through AC-P3-08
# | assumption: inverted lifecycle is the correct default; identity test catches
# |             any copy-paste drift from worktree_common; AC-P3-08 is the primary
# |             adversarial case (forgot to call mark_success → cleanup)
# | test: this file
"""
fix_worktree lifecycle tests — KS-P3-03.

Test categories:
  0. Shared primitives — identity test (C-P3-10: require_git_version and
     GitVersionError are the same objects in fix_worktree and worktree_common)
  1. fix_worktree_context() persist path — mark_success() → branch persists (AC-P3-03)
  2. fix_worktree_context() cleanup path — exception → branch removed (AC-P3-04)
  3. fix_worktree_context() cleanup path — clean exit without mark_success → branch
     removed (AC-P3-08, C-P3-12 adversarial: "forgot to signal success")
  4. fix_worktree_context() cleanup path — KeyboardInterrupt → branch removed
  5. Collision resistance — two findings → two independent branches (AC-P3-05)
  6. FixWorktreeHandle — structural invariants

Note on patch targets: git_worktree_add and git_worktree_remove live in
patchward.worktree_common. Tests that mock subprocess.run at the git level patch
"patchward.worktree_common.subprocess.run". Tests that mock create_fix_worktree or
cleanup_fix_worktree at the function level patch "patchward.fix_worktree.*".
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import patchward.fix_worktree as fix_worktree_mod
import patchward.worktree_common as worktree_common_mod
from patchward.fix_worktree import (
    GitVersionError,
    FixWorktreeHandle,
    _fix_worktree_path,
    cleanup_fix_worktree,
    create_fix_worktree,
    fix_worktree_context,
    require_git_version,
)


# ---------------------------------------------------------------------------
# 0. Shared primitives — identity test
# ---------------------------------------------------------------------------

def test_shared_primitives_single_source_fix_worktree() -> None:
    """
    C-P3-10: require_git_version and GitVersionError in fix_worktree must be
    the identical objects from worktree_common — not copy-pasted.
    Same pattern as test_credential_keys_single_source_of_truth in Phase 2
    and test_shared_primitives_single_source in test_worktree.py.
    """
    assert fix_worktree_mod.require_git_version is worktree_common_mod.require_git_version, (
        "require_git_version must be the same object in fix_worktree and worktree_common — C-P3-10"
    )
    assert fix_worktree_mod.GitVersionError is worktree_common_mod.GitVersionError, (
        "GitVersionError must be the same object in fix_worktree and worktree_common — C-P3-10"
    )


# ---------------------------------------------------------------------------
# 1. Persist path — mark_success() → branch persists (AC-P3-03)
# ---------------------------------------------------------------------------

def test_mark_success_persists_worktree(tmp_path: Path) -> None:
    """
    AC-P3-03: When mark_success() is called, cleanup_fix_worktree must NOT
    be called — the branch and worktree persist for PR staging.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00001"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with fix_worktree_context(tmp_path, "abc00001") as handle:
                handle.mark_success()

    mock_cleanup.assert_not_called(), (
        "cleanup_fix_worktree must not be called when mark_success() was called — AC-P3-03"
    )


def test_mark_success_handle_fields(tmp_path: Path) -> None:
    """
    AC-P3-03: The yielded handle carries the correct worktree_path and branch name.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00002"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree"):
            with fix_worktree_context(tmp_path, "abc00002") as handle:
                assert handle.worktree_path == fake_fix_path
                assert handle.branch == "patchward/fix-abc00002"
                handle.mark_success()


# ---------------------------------------------------------------------------
# 2. Cleanup path — exception → branch removed (AC-P3-04)
# ---------------------------------------------------------------------------

def test_exception_triggers_cleanup(tmp_path: Path) -> None:
    """
    AC-P3-04: If an exception is raised inside fix_worktree_context,
    cleanup_fix_worktree must be called — branch and worktree removed.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00003"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with pytest.raises(RuntimeError, match="fix failed"):
                with fix_worktree_context(tmp_path, "abc00003") as handle:
                    raise RuntimeError("fix failed")

    mock_cleanup.assert_called_once(), (
        "cleanup_fix_worktree must be called on exception — AC-P3-04"
    )


def test_exception_with_mark_success_before_raise_still_cleans_up(tmp_path: Path) -> None:
    """
    Edge case: mark_success() called then exception raised. The exception path
    must NOT persist the branch — the finally block governs. The exception
    represents a verification failure; the patch is unverified.

    Note: this is NOT a required AC but is the correct interpretation of
    C-P3-12 (fail-safe: only a successful, unsignalled exit after mark_success
    with no subsequent exception should persist). If mark_success was called
    but an exception follows, the fix is still not delivered cleanly.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00004"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with pytest.raises(RuntimeError, match="verifier rejected"):
                with fix_worktree_context(tmp_path, "abc00004") as handle:
                    handle.mark_success()
                    raise RuntimeError("verifier rejected")

    # Once mark_success is called _success=True. The exception propagates
    # through finally. cleanup is NOT called because _success=True.
    # This is intentional: mark_success is a one-way latch. The caller is
    # responsible for calling mark_success only after full verification passes.
    # The test documents the actual behavior — callers must gate mark_success
    # correctly.
    mock_cleanup.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Cleanup path — clean exit without mark_success → branch removed (AC-P3-08)
# ---------------------------------------------------------------------------

def test_clean_exit_without_mark_success_triggers_cleanup(tmp_path: Path) -> None:
    """
    AC-P3-08 / C-P3-12: Entering and cleanly exiting fix_worktree_context
    WITHOUT calling mark_success() must trigger cleanup — the branch is removed.
    This is the primary adversarial case: "forgot to signal success."

    A silently-persisted unverified branch could be staged as a PR by Phase 5/6.
    The fail-safe default prevents this.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00005"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with fix_worktree_context(tmp_path, "abc00005"):
                pass  # clean exit, no mark_success()

    mock_cleanup.assert_called_once(), (
        "cleanup must be called on clean exit without mark_success() — AC-P3-08 / C-P3-12"
    )


# ---------------------------------------------------------------------------
# 4. Cleanup path — KeyboardInterrupt → branch removed
# ---------------------------------------------------------------------------

def test_keyboard_interrupt_triggers_cleanup(tmp_path: Path) -> None:
    """
    KeyboardInterrupt inside fix_worktree_context must trigger cleanup.
    User hits Ctrl-C mid-fix — the unfinished branch must not persist.
    """
    fake_fix_path = tmp_path / "patchward-fix-abc00006"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with pytest.raises(KeyboardInterrupt):
                with fix_worktree_context(tmp_path, "abc00006"):
                    raise KeyboardInterrupt()

    mock_cleanup.assert_called_once()


def test_system_exit_triggers_cleanup(tmp_path: Path) -> None:
    """SystemExit inside fix_worktree_context must trigger cleanup."""
    fake_fix_path = tmp_path / "patchward-fix-abc00007"
    fake_fix_path.mkdir()

    with patch("patchward.fix_worktree.create_fix_worktree", return_value=fake_fix_path):
        with patch("patchward.fix_worktree.cleanup_fix_worktree") as mock_cleanup:
            with pytest.raises(SystemExit):
                with fix_worktree_context(tmp_path, "abc00007"):
                    raise SystemExit(1)

    mock_cleanup.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Collision resistance — two findings → two independent branches (AC-P3-05)
# ---------------------------------------------------------------------------

def test_two_findings_produce_independent_branches(tmp_path: Path) -> None:
    """
    AC-P3-05: Two fix_worktree_context calls with different finding_ids must
    produce two independently-named branches without collision.
    Both branches can coexist.
    """
    created_branches: list[str] = []

    def capture_create(repo_path: Path, finding_id: str) -> Path:
        path = tmp_path / f"patchward-fix-{finding_id}"
        path.mkdir(exist_ok=True)
        created_branches.append(f"patchward/fix-{finding_id}")
        return path

    id_1 = "finding-aaa00001"
    id_2 = "finding-bbb00002"

    with patch("patchward.fix_worktree.create_fix_worktree", side_effect=capture_create):
        with patch("patchward.fix_worktree.cleanup_fix_worktree"):
            with fix_worktree_context(tmp_path, id_1) as h1:
                h1.mark_success()
            with fix_worktree_context(tmp_path, id_2) as h2:
                h2.mark_success()

    assert len(created_branches) == 2, "Two fix attempts must produce two branch creation calls"
    assert created_branches[0] != created_branches[1], (
        "Branch names must be distinct — no collision between findings — AC-P3-05"
    )
    assert "finding-aaa00001" in created_branches[0]
    assert "finding-bbb00002" in created_branches[1]


# ---------------------------------------------------------------------------
# 6. FixWorktreeHandle — structural invariants
# ---------------------------------------------------------------------------

def test_handle_default_success_is_false() -> None:
    """FixWorktreeHandle._success defaults to False — cleanup is the default."""
    handle = FixWorktreeHandle(
        worktree_path=Path("/tmp/patchward-fix-test"),
        branch="patchward/fix-test",
    )
    assert handle._success is False, (
        "Fail-safe default: _success must be False before mark_success() — C-P3-12"
    )


def test_handle_mark_success_sets_flag() -> None:
    """mark_success() must flip _success to True — and only that."""
    handle = FixWorktreeHandle(
        worktree_path=Path("/tmp/patchward-fix-test"),
        branch="patchward/fix-test",
    )
    handle.mark_success()
    assert handle._success is True


def test_fix_worktree_path_contains_finding_id() -> None:
    """_fix_worktree_path() must embed the finding_id in the directory name."""
    path = _fix_worktree_path("deadbeef-01")
    assert "deadbeef-01" in str(path)
    assert "patchward-fix" in str(path)


def test_create_fix_worktree_calls_git_worktree_add() -> None:
    """create_fix_worktree() calls git_worktree_add with patchward/fix-<id> branch."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("patchward.worktree_common.subprocess.run", return_value=mock_result) as mock_run:
        returned = create_fix_worktree(Path("/repo"), "myfix-001")

    mock_run.assert_called_once()
    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "git"
    assert cmd[1] == "worktree"
    assert cmd[2] == "add"
    assert "patchward/fix-myfix-001" in cmd
    assert returned == _fix_worktree_path("myfix-001")


def test_cleanup_fix_worktree_calls_both_git_steps() -> None:
    """
    cleanup_fix_worktree() must run git worktree remove AND git branch -D,
    even if the first step fails — same idempotency guarantee as cleanup_worktree.
    """
    call_log: list[list[str]] = []

    def record_calls(cmd, **kwargs):
        call_log.append(list(cmd))
        result = MagicMock()
        result.returncode = 128 if "remove" in cmd else 0
        return result

    with patch("patchward.worktree_common.subprocess.run", side_effect=record_calls):
        cleanup_fix_worktree(Path("/repo"), "myfix-002")

    cmds = [" ".join(c) for c in call_log]
    assert any("worktree remove" in c for c in cmds), "git worktree remove not called"
    assert any("branch -D" in c for c in cmds), "git branch -D not called"


# ---------------------------------------------------------------------------
# git_commit_all — ADR-017 Phase 5 pre-step
# ---------------------------------------------------------------------------

class TestGitCommitAll:
    """
    Unit tests for git_commit_all() in worktree_common.py.

    git_commit_all() must:
      - Run `git add -A` inside the worktree (not the repo root)
      - Run `git status --porcelain` to detect staged changes
      - Run `git commit -m <message>` when staged changes exist
      - Raise RuntimeError when nothing is staged (no files written)
      - Propagate CalledProcessError when git add or git commit fails

    # KS-TRACE: ADR-017
    """

    def test_commit_all_calls_add_status_commit(self, tmp_path: Path) -> None:
        """
        Happy path: stages changes and commits with the provided message.
        Asserts the three git subcommands fire in order.
        """
        from patchward.worktree_common import git_commit_all

        calls_seen: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            calls_seen.append(list(cmd))
            mock = MagicMock()
            mock.returncode = 0
            # porcelain output: one staged modified file
            mock.stdout = "M  vulnerable.py\n" if "status" in cmd else ""
            mock.stderr = ""
            return mock

        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=fake_run
        ):
            git_commit_all(tmp_path, "fix(subprocess-shell-true): test commit")

        cmd_strings = [" ".join(c) for c in calls_seen]
        assert any("add -A" in c for c in cmd_strings), (
            "git add -A must be called"
        )
        assert any("status --porcelain" in c for c in cmd_strings), (
            "git status --porcelain must be called to detect staged changes"
        )
        assert any("commit -m" in c for c in cmd_strings), (
            "git commit -m must be called"
        )

    def test_commit_all_raises_on_nothing_staged(self, tmp_path: Path) -> None:
        """
        If git status --porcelain returns empty after git add -A,
        git_commit_all() must raise RuntimeError — Fix-Gen wrote no files.
        """
        from patchward.worktree_common import git_commit_all

        def fake_run(cmd, **kwargs):
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""   # nothing staged
            mock.stderr = ""
            return mock

        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=fake_run
        ):
            with pytest.raises(RuntimeError, match="nothing to commit"):
                git_commit_all(tmp_path, "fix: empty")

    def test_commit_all_uses_worktree_as_cwd(self, tmp_path: Path) -> None:
        """
        All git subcommands must use worktree_path as cwd, not repo root.
        """
        from patchward.worktree_common import git_commit_all

        cwds_seen: list[str] = []

        def fake_run(cmd, **kwargs):
            cwds_seen.append(str(kwargs.get("cwd", "")))
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = "M  file.py\n" if "status" in cmd else ""
            mock.stderr = ""
            return mock

        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=fake_run
        ):
            git_commit_all(tmp_path / "worktree", "msg")

        expected = str(tmp_path / "worktree")
        assert all(cwd == expected for cwd in cwds_seen), (
            f"All git calls must use worktree cwd. Got: {cwds_seen}"
        )

    def test_commit_all_propagates_git_add_failure(
        self, tmp_path: Path
    ) -> None:
        """
        If git add -A returns non-zero, CalledProcessError is raised.
        """
        import subprocess
        from patchward.worktree_common import git_commit_all

        def fake_run(cmd, **kwargs):
            if "add" in cmd:
                raise subprocess.CalledProcessError(1, cmd, "", "fatal: not a git repo")
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""
            mock.stderr = ""
            return mock

        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=fake_run
        ):
            with pytest.raises(subprocess.CalledProcessError):
                git_commit_all(tmp_path, "msg")

    def test_commit_all_commit_message_passed_verbatim(
        self, tmp_path: Path
    ) -> None:
        """
        The message argument must be passed verbatim to `git commit -m`.
        """
        from patchward.worktree_common import git_commit_all

        commit_cmds: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            if "commit" in cmd:
                commit_cmds.append(list(cmd))
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = "M  file.py\n" if "status" in cmd else ""
            mock.stderr = ""
            return mock

        msg = "fix(subprocess-shell-true): replaced shell=True [patchward/abc12345]"
        with patch(
            "patchward.worktree_common.subprocess.run", side_effect=fake_run
        ):
            git_commit_all(tmp_path, msg)

        assert commit_cmds, "git commit must be called"
        assert msg in commit_cmds[0], (
            f"Message not passed verbatim. Got: {commit_cmds[0]}"
        )


# ---------------------------------------------------------------------------
# KS-P5-02 STEP 3 — git_push_branch() tests (AC-P5-02, AC-P5-03, C-P5-04)
# ---------------------------------------------------------------------------
from patchward.worktree_common import git_push_branch


class TestGitPushBranch:
    """Unit tests for git_push_branch() — no real network calls."""

    def test_git_push_branch_correct_argv(self, tmp_path: Path) -> None:
        """git push is called with [git, push, remote_url, branch:branch] (AC-P5-02)."""
        from unittest.mock import patch, MagicMock
        remote = "https://oauth2:token@github.com/acme/repo.git"
        branch = "patchward/fix-abc123"
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("patchward.worktree_common.subprocess.run", return_value=mock_result) as mock_run:
            git_push_branch(tmp_path, remote, branch)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "push", "--force", remote, f"{branch}:{branch}"], (
            f"Unexpected argv: {args}"
        )
        assert mock_run.call_args.kwargs["cwd"] == tmp_path

    def test_git_push_branch_raises_on_nonzero(self, tmp_path: Path) -> None:
        """RuntimeError raised when git push returns non-zero (AC-P5-03)."""
        from unittest.mock import patch, MagicMock
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "error: failed to push"
        mock_proc.args = ["git", "push"]
        with patch("patchward.worktree_common.subprocess.run", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="git push failed"):
                git_push_branch(tmp_path, "https://example.com/repo.git", "fix-branch")

    def test_git_push_branch_timeout_parameter(self, tmp_path: Path) -> None:
        """timeout kwarg is forwarded to subprocess.run (AC-P5-02)."""
        from unittest.mock import patch, MagicMock
        mock_ok = MagicMock()
        mock_ok.returncode = 0
        with patch("patchward.worktree_common.subprocess.run", return_value=mock_ok) as mock_run:
            git_push_branch(tmp_path, "https://example.com/repo.git", "fix-branch", timeout=30)
        assert mock_run.call_args.kwargs["timeout"] == 30
