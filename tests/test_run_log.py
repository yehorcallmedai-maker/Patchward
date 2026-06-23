# KS-TRACE: AC-P3-11
# | assumption: NDJSON append preserves byte-identity of prior records;
# |             parent directory creation is lazy (happens on first append)
# | test: this file
"""
Run log tests — AC-P3-11.

Verified:
  - Two sequential appends → two records, order preserved.
  - First record byte-identical before and after second append.
  - Empty log → records() returns [].
  - Parent directory created automatically on first append.
  - Record fields are preserved exactly.
  - Path property returns the configured path.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from repomend.run_log import RunLog

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _record(n: int = 1) -> dict:
    return {
        "finding_id": f"test-{n:03d}",
        "file_path": f"src/module_{n}.py",
        "rule_id": "some.rule",
        "severity": "error",
        "model_used": "claude-opus-4-8",
        "branch_name": f"repomend/fix-{n:03d}",
        "success": True,
        "timestamp": f"2026-06-12T00:0{n}:00+00:00",
    }


# ---------------------------------------------------------------------------
# AC-P3-11: core invariants
# ---------------------------------------------------------------------------

def test_run_log_empty_returns_empty_list(tmp_path: Path) -> None:
    """records() on a log that has never been written returns []."""
    log = RunLog(tmp_path / "never_written.json")
    assert log.records() == []


def test_run_log_single_append_one_record(tmp_path: Path) -> None:
    """After one append, records() returns exactly one record."""
    log = RunLog(tmp_path / "run.json")
    log.append(_record(1))
    records = log.records()
    assert len(records) == 1
    assert records[0]["finding_id"] == "test-001"


def test_run_log_two_appends_two_records_ordered(tmp_path: Path) -> None:
    """
    Two sequential appends → two records in insertion order.
    Invariant: first record is unchanged after second append.
    """
    log = RunLog(tmp_path / "run.json")
    log.append(_record(1))

    # Capture raw bytes of log file after first write
    raw_after_first = log.path.read_bytes()

    log.append(_record(2))

    records = log.records()
    assert len(records) == 2
    assert records[0]["finding_id"] == "test-001"
    assert records[1]["finding_id"] == "test-002"

    # The bytes that existed before the second append must still be present at
    # the same offset — true append-only (AC-P3-11 primary invariant).
    raw_after_second = log.path.read_bytes()
    assert raw_after_second[: len(raw_after_first)] == raw_after_first, (
        "First record bytes were mutated by second append — append-only invariant violated"
    )


def test_run_log_record_fields_preserved(tmp_path: Path) -> None:
    """All required record fields are written and read back unchanged."""
    log = RunLog(tmp_path / "run.json")
    rec = _record(1)
    log.append(rec)
    read_back = log.records()[0]
    for key, value in rec.items():
        assert read_back[key] == value, f"Field '{key}' mismatch: {read_back[key]!r} != {value!r}"


def test_run_log_creates_parent_directory(tmp_path: Path) -> None:
    """Parent directory is created automatically on first append."""
    nested = tmp_path / "deep" / "nested" / "run.json"
    assert not nested.parent.exists()
    log = RunLog(nested)
    log.append(_record(1))
    assert nested.exists()
    assert len(log.records()) == 1


def test_run_log_path_property(tmp_path: Path) -> None:
    """path property returns the configured path."""
    p = tmp_path / "explicit.json"
    log = RunLog(p)
    assert log.path == p


def test_run_log_multiple_instances_same_file(tmp_path: Path) -> None:
    """Two separate RunLog instances pointing to the same file both append correctly."""
    p = tmp_path / "shared.json"
    log_a = RunLog(p)
    log_b = RunLog(p)

    log_a.append(_record(1))
    log_b.append(_record(2))

    records = RunLog(p).records()
    assert len(records) == 2
    assert {r["finding_id"] for r in records} == {"test-001", "test-002"}


def test_run_log_default_path_in_runs_dir() -> None:
    """Default path is inside runs/ directory with session_ prefix."""
    log = RunLog()
    assert "runs" in str(log.path)
    assert log.path.name.startswith("session_")
    assert log.path.suffix == ".json"


def test_run_log_ndjson_one_line_per_record(tmp_path: Path) -> None:
    """Each append produces exactly one line in the file (NDJSON format)."""
    log = RunLog(tmp_path / "run.json")
    log.append(_record(1))
    log.append(_record(2))
    log.append(_record(3))
    lines = [l for l in log.path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 3, f"Expected 3 NDJSON lines, got {len(lines)}"


# ── KS-P6-06: append_batch_result ─────────────────────────────────────────

def test_append_batch_result_writes_repo_field(tmp_path):
    """
    append_batch_result() writes the 'repo' field to the NDJSON log.
    # KS-TRACE: AC-P6-09, C-P6-09
    """
    from repomend.run_log import RunLog

    log = RunLog(path=tmp_path / "batch.json")
    log.append_batch_result({"repo": "acme/foo", "status": "pr_opened"})

    records = log.records()
    assert len(records) == 1
    assert records[0]["repo"] == "acme/foo"
    assert records[0]["status"] == "pr_opened"


def test_append_batch_result_adds_timestamp(tmp_path):
    """
    append_batch_result() injects a 'timestamp' field into the record.
    # KS-TRACE: AC-P6-09, C-P6-09
    """
    from repomend.run_log import RunLog

    log = RunLog(path=tmp_path / "batch.json")
    log.append_batch_result({"repo": "acme/bar", "status": "ok"})

    records = log.records()
    assert "timestamp" in records[0]
    # Must be a non-empty ISO 8601-style string
    ts = records[0]["timestamp"]
    assert isinstance(ts, str) and len(ts) > 10


def test_append_batch_result_does_not_mutate_input(tmp_path):
    """
    append_batch_result() must not modify the caller's result dict.
    """
    from repomend.run_log import RunLog

    log = RunLog(path=tmp_path / "batch.json")
    result = {"repo": "acme/baz", "status": "no_findings"}
    log.append_batch_result(result)
    assert "timestamp" not in result
