# KS-TRACE: C-P3-09, C-P3-10, C-P3-11, C-P3-12
# | assumption: inverted lifecycle (persist on success, cleanup on failure) is the
# |             correct default for fix branches — deny-by-default posture;
# |             finding_id includes a uuid4 slug so branch names never collide;
# |             shared primitives imported from worktree_common — identity test enforces this
# | test: test_fix_worktree.py
"""
Fix-path git worktree lifecycle for Phase 3 Fix-Gen subagent.

Every fix attempt operates on a `patchward/fix-<finding-id>` worktree branch.
The lifecycle is INVERTED relative to worktree.py's scan lifecycle:

  worktree.py     — always cleans up (finally block, both success and failure)
  fix_worktree.py — persists on success (.mark_success() called), cleans up on
                    any other exit (exception, clean exit without mark_success,
                    KeyboardInterrupt, SystemExit)

Lifecycle contract (C-P3-12):
  - Default = cleanup. An unsigned exit is an unverified fix.
  - Explicit .mark_success() call required to persist the branch.
  - Unverified fixes must never silently become PR-source branches.

Checkpoint semantics (C-P3-11):
  - The clean worktree state at context entry IS the checkpoint (git HEAD).
  - Rollback on exception: worktree + branch discarded entirely (no reset needed).
  - No .bak files, no runs/checkpoints/ directory — git is the version-control
    primitive.

Shared primitives rule (C-P3-10):
  - git_worktree_add, git_worktree_remove, require_git_version, GitVersionError
    are imported from worktree_common — not duplicated here.
  - A unit test asserts identity (is) of require_git_version and GitVersionError
    across worktree_common, worktree, and fix_worktree.

Usage::

    from patchward.fix_worktree import fix_worktree_context

    with fix_worktree_context(repo_path, finding_id) as handle:
        # apply patch to handle.worktree_path / finding["file_path"]
        handle.mark_success()   # branch persists after context exits
    # if mark_success() was not called: worktree + branch removed here
"""
from __future__ import annotations

import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from patchward.worktree_common import (
    GitVersionError,
    git_worktree_add,
    git_worktree_remove,
    require_git_version,
)

__all__ = [
    "GitVersionError",
    "require_git_version",
    "_fix_worktree_path",
    "create_fix_worktree",
    "cleanup_fix_worktree",
    "FixWorktreeHandle",
    "fix_worktree_context",
]


def _fix_worktree_path(finding_id: str) -> Path:
    """
    Deterministic temp path for a fix worktree.
    Consistent between create_fix_worktree and cleanup_fix_worktree
    for a given finding_id.
    """
    return Path(tempfile.gettempdir()) / f"patchward-fix-{finding_id}"


def create_fix_worktree(repo_path: Path, finding_id: str) -> Path:
    """
    Create a git worktree on branch `patchward/fix-{finding_id}`.

    Args:
        repo_path:  Path to the git repository root.
        finding_id: Unique identifier for this finding (e.g. rule_id slug + uuid4 short).
                    Must be globally unique across concurrent fix attempts.

    Returns:
        Path to the created worktree (temp directory).

    Raises:
        subprocess.CalledProcessError: If `git worktree add` fails.

    # KS-TRACE: C-P3-10, C-P3-11
    """
    fix_path = _fix_worktree_path(finding_id)
    git_worktree_add(repo_path, fix_path, f"patchward/fix-{finding_id}")
    return fix_path


def cleanup_fix_worktree(repo_path: Path, finding_id: str) -> None:
    """
    Remove the worktree and delete the `patchward/fix-{finding_id}` branch.

    Idempotent: does not raise if the worktree or branch does not exist.
    Both steps run regardless of whether the first succeeds.

    # KS-TRACE: C-P3-10, C-P3-11, C-P3-12
    """
    git_worktree_remove(
        repo_path,
        _fix_worktree_path(finding_id),
        f"patchward/fix-{finding_id}",
    )


@dataclass
class FixWorktreeHandle:
    """
    Handle yielded by fix_worktree_context. Holds the worktree path and branch
    name, and provides .mark_success() to signal that the fix was verified and
    the branch should persist.

    C-P3-12: Fail-safe default — cleanup unless mark_success() is called.
    """

    worktree_path: Path
    branch: str
    _success: bool = field(default=False, init=False, repr=False)

    def mark_success(self) -> None:
        """
        Signal that the fix was applied and verified. The worktree and branch
        will persist after fix_worktree_context exits, available for PR staging.

        Must be called explicitly — clean context exit without this call is
        treated as failure and triggers cleanup (C-P3-12).
        """
        self._success = True


@contextmanager
def fix_worktree_context(
    repo_path: Path,
    finding_id: str,
) -> Generator[FixWorktreeHandle, None, None]:
    """
    Context manager implementing the inverted-lifecycle fix worktree pattern.

    Creates a `patchward/fix-{finding_id}` worktree, yields a FixWorktreeHandle,
    then either persists or discards the worktree depending on whether
    handle.mark_success() was called.

    Persist path (mark_success() called):
      - Worktree and branch survive context exit.
      - Caller receives handle.worktree_path and handle.branch for PR staging.

    Cleanup path (all other exits — C-P3-12 fail-safe default):
      - Clean exit without mark_success() → cleanup.
      - Exception raised inside block → cleanup.
      - KeyboardInterrupt → cleanup.
      - SystemExit → cleanup.

    Args:
        repo_path:  Path to the git repository root.
        finding_id: Unique identifier for this finding.

    Yields:
        FixWorktreeHandle with .worktree_path, .branch, and .mark_success().

    # KS-TRACE: C-P3-10, C-P3-11, C-P3-12
    """
    fix_path = create_fix_worktree(repo_path, finding_id)
    handle = FixWorktreeHandle(
        worktree_path=fix_path,
        branch=f"patchward/fix-{finding_id}",
    )
    try:
        yield handle
    finally:
        # C-P3-12: persist only if mark_success() was explicitly called.
        # Any other exit — clean, exception, KeyboardInterrupt, SystemExit —
        # triggers cleanup. An unsigned exit is an unverified fix.
        if not handle._success:
            cleanup_fix_worktree(repo_path, finding_id)
