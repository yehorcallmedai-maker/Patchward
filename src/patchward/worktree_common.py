# KS-TRACE: C-P3-10, C-P3-11
# | assumption: both worktree.py (scan path) and fix_worktree.py (fix path) import from
# |             this module — identity test in test_worktree.py enforces no drift
# | test: test_worktree.py (identity test), test_fix_worktree.py
"""
Shared git worktree primitives for patchward.worktree and patchward.fix_worktree.

This module is the single source of truth for:
  - GitVersionError / require_git_version()
  - git_worktree_add()    — raw `git worktree add` invocation
  - git_worktree_remove() — raw `git worktree remove --force` + `git branch -D`
  - git_commit_all()      — stage all changes and commit inside a worktree

Both worktree.py (scan path: patchward/scan-<id>) and fix_worktree.py
(fix path: patchward/fix-<finding-id>) import from here. Neither duplicates
these implementations.

A unit test asserts identity (is, not ==) of require_git_version and
GitVersionError to catch drift — same pattern as
test_credential_keys_single_source_of_truth in Phase 2.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


class GitVersionError(RuntimeError):
    """
    Raised by require_git_version() when git is not available or is too old.
    git 2.5+ is required for worktree support.
    """


def require_git_version(min_version: tuple[int, int] = (2, 5)) -> None:
    """
    Fail-fast: check that git >= min_version is available on PATH.
    Raises GitVersionError with actionable message if not.

    Same pattern as _require_tool() in scanner.py and require_docker() in
    docker_sandbox.py. Call once at CLI startup before any worktree operations.

    # KS-TRACE: C-P2-05, C-P3-10
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise GitVersionError(
            "git not found on PATH. Install git: https://git-scm.com/downloads"
        )

    m = re.search(r"git version (\d+)\.(\d+)", result.stdout)
    if not m:
        raise GitVersionError(
            f"Could not parse git version from output: "
            f"{result.stdout.strip()!r}"
        )

    major, minor = int(m.group(1)), int(m.group(2))
    if (major, minor) < min_version:
        raise GitVersionError(
            f"git 2.5+ required for worktree support. "
            f"Found: {result.stdout.strip()}"
        )


def git_worktree_add(
    repo_path: Path, worktree_path: Path, branch: str
) -> None:
    """
    Raw `git worktree add <worktree_path> -b <branch>`.

    Caller is responsible for choosing the branch name and worktree path.
    This function is agnostic to scan-vs-fix naming conventions.

    Args:
        repo_path:     Path to the git repository root (used as cwd).
        worktree_path: Absolute path where the worktree will be created.
        branch:        Full branch name, e.g. 'patchward/scan-abc12345'
                       or 'patchward/fix-<finding-id>'.

    Raises:
        subprocess.CalledProcessError: If `git worktree add` fails.

    # KS-TRACE: C-P3-10, C-P3-11
    """
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Self-heal: if the branch already exists (stale from a previous run
        # whose cleanup silently failed on Windows), delete it and retry once.
        if "already exists" in result.stderr:
            # Remove the stale worktree directory first (required before
            # branch delete)
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(repo_path),
                capture_output=True,
            )
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=str(repo_path),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=str(repo_path),
                capture_output=True,
            )
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch],
                cwd=str(repo_path),
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            raise subprocess.CalledProcessError(
                result.returncode, result.args, result.stdout, result.stderr
            )


def git_commit_all(worktree_path: Path, message: str) -> None:
    """
    Stage all changes in the worktree and create a commit.

    Equivalent to `git add -A && git commit -m <message>` run inside the
    worktree directory. Uses the worktree path as cwd so git operates on
    the correct branch without needing the repo_path.

    Required before Phase 5 PR push: fix branches must have at least one
    commit of their own. Currently fix_gen.py writes patches as uncommitted
    working-tree changes — this helper converts them to a commit.

    Args:
        worktree_path: Absolute path to the fix worktree.
        message:       Commit message. Convention: first line ≤ 72 chars.

    Raises:
        subprocess.CalledProcessError: If `git add` or `git commit` fails.
        RuntimeError: If the worktree has no changes to commit (nothing
                      staged after `git add -A`). This indicates Fix-Gen
                      did not actually write any files — a logic error that
                      should surface as a test failure, not silently pass.

    # KS-TRACE: ADR-017, Phase 5 pre-step
    """
    # Stage all changes (new, modified, deleted)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(worktree_path),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Check whether there is anything to commit
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # After `git add -A`, staged changes appear as lines starting with
    # a letter in column 1 (e.g. 'M ', 'A ', 'D ').  If porcelain is
    # empty after add, the worktree was already clean — nothing to commit.
    staged = [
        ln for ln in status.stdout.splitlines()
        if ln and ln[0] != " " and ln[0] != "?"
    ]
    if not staged:
        raise RuntimeError(
            f"git_commit_all: nothing to commit in {worktree_path}. "
            "Fix-Gen did not write any files before submit_fix was called."
        )

    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(worktree_path),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_worktree_remove(
    repo_path: Path, worktree_path: Path, branch: str
) -> None:
    """
    Remove a git worktree and delete its branch. Idempotent.

    Runs both `git worktree remove --force` and `git branch -D` regardless
    of whether the first step succeeds (e.g. worktree already gone but
    branch still exists). Neither step raises on missing targets.

    Args:
        repo_path:     Path to the git repository root (used as cwd).
        worktree_path: Absolute path of the worktree to remove.
        branch:        Full branch name to delete.

    # KS-TRACE: C-P3-10, C-P3-11
    """
    # Step 1: remove worktree — no check=True, idempotent
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=str(repo_path),
        capture_output=True,
    )

    # Step 2: delete branch — no check=True, idempotent
    subprocess.run(
        ["git", "branch", "-D", branch],
        cwd=str(repo_path),
        capture_output=True,
    )

def git_push_branch(
    repo_path: Path,
    remote_url: str,
    branch_name: str,
    timeout: int = 60,
) -> None:
    """
    Push branch_name to remote_url from repo_path.

    Raises subprocess.CalledProcessError on non-zero exit so callers can
    catch and log pr_status: push_failed without crashing the process.

    The remote_url must have credentials embedded by the caller —
    this function is credential-agnostic and never constructs URLs.
    The URL is passed directly to git push and is never logged here.

    Args:
        repo_path:   Root of the git repository (not the worktree).
        remote_url:  Full HTTPS remote URL, credentials embedded by caller.
        branch_name: Local branch name; pushed as branch_name:branch_name.
        timeout:     Wall-clock seconds before the push is killed (default 60).

    Raises:
        subprocess.CalledProcessError: git push returned non-zero.
        subprocess.TimeoutExpired:     push exceeded timeout.

    # KS-TRACE: AC-P5-02, AC-P5-03, C-P5-02, C-P5-04, ADR-018
    """
    proc = subprocess.run(
        ["git", "push", "--force", remote_url, f"{branch_name}:{branch_name}"],
        cwd=repo_path,
        check=False,
        capture_output=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git push failed (exit {proc.returncode})\n"
            f"stdout: {proc.stdout!r}\n"
            f"stderr: {proc.stderr!r}"
        )
