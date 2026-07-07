# KS-TRACE: AC-P3-11
# | assumption: NDJSON (one JSON line per record) is truly append-only — existing
# |             records are never read or mutated during a write; byte-identity holds.
# | test: test_run_log.py
"""
Append-only run log for Fix-Gen sessions (AC-P3-11).

Format: NDJSON — one JSON object per line, newline-terminated.
Path:   runs/session_<UTC-timestamp>.json

One RunLog instance per Fix-Gen session. Each apply_fix() attempt appends one record.

Record shape::

    {
        "finding_id":  str,   # Fix-Gen invocation identifier
        "file_path":   str,   # finding file path
        "rule_id":     str,   # scanner rule ID
        "severity":    str,   # SARIF level: "error" | "warning" | "note"
        "model_used":  str,   # model that generated the fix
        "branch_name": str,   # patchward/fix-<id> branch
        "success":     bool,  # True = submit_fix called; False = exhausted / failed
        "timestamp":   str,   # ISO 8601 UTC
    }

Append-only invariant: append() opens the file in append mode ("a").
It NEVER reads the file, NEVER rewrites existing content.
First record byte position is unchanged after any subsequent append.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_LOG_DIR = Path("runs")


def _default_session_path() -> Path:
    """Generate a timestamp-stamped path for a new session log."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _DEFAULT_LOG_DIR / f"session_{ts}.json"


class RunLog:
    """
    Append-only NDJSON run log for one Fix-Gen session.

    # KS-TRACE: AC-P3-11 | assumption: single writer per session; no locking needed
    """

    def __init__(self, path: Path | None = None) -> None:
        """
        Args:
            path: Explicit log file path. Defaults to runs/session_<timestamp>.json.
                  Parent directory is created on first append (not at construction time).
        """
        self._path: Path = path if path is not None else _default_session_path()

    @property
    def path(self) -> Path:
        return self._path

    def append(self, record: dict[str, Any]) -> None:
        """
        Append one record as a single JSON line.

        Opens the file in append mode — existing content is NEVER modified.
        Creates parent directories and the file on first call.

        # KS-TRACE: AC-P3-11 | invariant: first record byte-identical after second append
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, separators=(",", ":")) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)


    def append_batch_result(self, result: dict[str, Any]) -> None:
        """
        Append one batch-pipeline result dict as a single JSON line.

        Adds a ``timestamp`` field (ISO 8601 UTC) to the record so
        per-repo batch results can be correlated with wall-clock time.
        The ``result`` dict itself is not mutated — a copy is written.

        # KS-TRACE: AC-P6-09, C-P6-09
        """
        record = dict(result)
        record["timestamp"] = datetime.now(
            tz=timezone.utc
        ).isoformat()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, separators=(",", ":")) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    def read_all(self) -> list[dict[str, Any]]:
        """
        Return all NDJSON records as a list.

        Alias for ``records()`` — named for explicitness in
        integration tests that assert record count.

        # KS-TRACE: AC-P6-11
        """
        return self.records()

    def records(self) -> list[dict[str, Any]]:
        """Return all records as a list (for testing / reporting)."""
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]
