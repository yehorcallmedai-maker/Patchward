# KS-TRACE: C-P2-05, C-P2-08, AC-P2-06
# | assumption: cleanup idempotency covers all exit paths including signals and hook denials;
# |             KeyboardInterrupt propagates through finally so worktree is always removed;
# |             git 2.5+ available on dev machine before KS-P2-06 runs
# | test: test_worktree.py
"""
git worktree isolation for Phase 2 scanner subprocess isolation.

Every scan operates on a `repomend/scan-<id>` worktree branch.
The caller's working branch is never touched. The worktree is
always removed in a finally block — on clean exit, exception,
hook denial (DeniedToolCallError), and KeyboardInterrupt.

Trust invariants enforced here:
  C-P2-05  Every scan operates on a git worktree, not the caller's working branch.
  C-P2-08  Caller's working branch is identical before and after scan.

Shared git primitives (require_git_version, GitVersionError, git_worktree_add,
git_worktree_remove) live in worktree_common.py and are imported here.
This module contains only scan-specific naming logic (repomend/scan-<id>).

Usage::

    from repomend.worktree import require_git_version, worktree_context

    require_git_version()  # call once at CLI startup

    with worktree_context(repo_path) as scan_path:
        sarif_runs = run_all_scanners(scan_path)
    # worktree removed here regardless of how the block exits
"""
from __future__ import annotations

import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from repomend.worktree_common import (
    GitVersionError,
    git_worktree_add,
    git_worktree_remove,
    require_git_version,
)

__all__ = [
    "GitVersionError",
    "require_git_version",
    "_worktree_path",
    "create_worktree",
    "cleanup_worktree",
    "worktree_context",
]


def _worktree_path(scan_id: str) -> Path:
    """
    Deterministic temp path for a scan worktree.
    Consistent between create_worktree and cleanup_worktree for a given scan_id.
    """
    return Path(tempfile.gettempdir()) / f"repomend-scan-{scan_id}"


def create_worktree(repo_path: Path, scan_id: str) -> Path:
    """
    Create a git worktree on branch `repomend/scan-{scan_id}`.

    Args:
        repo_path: Path to the git repository root.
        scan_id:   Short unique identifier for this scan (e.g. uuid4().hex[:8]).

    Returns:
        Path to the created worktree (temp directory).

    Raises:
        subprocess.CalledProcessError: If `git worktree add` fails.

    # KS-TRACE: C-P2-05, AC-P2-06
    """
    scan_path = _worktree_path(scan_id)
    git_worktree_add(repo_path, scan_path, f"repomend/scan-{scan_id}")
    return scan_path


def cleanup_worktree(repo_path: Path, scan_id: str) -> None:
    """
    Remove the worktree and delete the `repomend/scan-{scan_id}` branch.

    Idempotent: does not raise if the worktree or branch does not exist
    (e.g. if called twice, or if create_worktree was never completed).
    Both steps run regardless of whether the first succeeds.

    # KS-TRACE: C-P2-05, C-P2-08, AC-P2-06
    """
    git_worktree_remove(repo_path, _worktree_path(scan_id), f"repomend/scan-{scan_id}")


@contextmanager
def worktree_context(repo_path: Path) -> Generator[Path, None, None]:
    """
    Context manager that creates a scan worktree, yields its path, and
    ALWAYS cleans up in a finally block.

    Cleanup runs on:
      - Clean exit
      - Any exception (including DeniedToolCallError from hooks.py)
      - KeyboardInterrupt
      - SystemExit

    No `repomend/scan-*` branch or worktree directory is ever leaked.

    Args:
        repo_path: Path to the git repository root.

    Yields:
        Path to the isolated worktree. Pass this to run_all_scanners().
        Never pass the original repo_path to any scanner directly.

    # KS-TRACE: C-P2-05, C-P2-08, AC-P2-06
    """
    scan_id = uuid.uuid4().hex[:8]
    scan_path = create_worktree(repo_path, scan_id)
    try:
        yield scan_path
    finally:
        # Must run under ALL exit conditions — this is the correctness invariant.
        # A leaked repomend/scan-* branch on the caller's repo is a violation
        # regardless of why the scan failed.
        cleanup_worktree(repo_path, scan_id)
