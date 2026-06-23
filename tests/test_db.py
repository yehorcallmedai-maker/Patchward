# KS-TRACE: AC-02, AC-03, ADR-008 | test: SQLite state store — schema, run lifecycle, findings
from __future__ import annotations

from pathlib import Path

import pytest

from repomend.db import (
    open_db,
    get_or_create_repo,
    create_run,
    finish_run,
    insert_finding,
    SCHEMA_VERSION,
)


@pytest.fixture()
def db(tmp_path: Path):
    conn = open_db(tmp_path / "state.db")
    yield conn
    conn.close()


def test_schema_version_written(db) -> None:
    row = db.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
    assert row["v"] == SCHEMA_VERSION


def test_get_or_create_repo_idempotent(db) -> None:
    id1 = get_or_create_repo(db, "/some/repo")
    id2 = get_or_create_repo(db, "/some/repo")
    assert id1 == id2


def test_create_run_recorded(db) -> None:
    repo_id = get_or_create_repo(db, "/repo/a")
    run_id = create_run(db, repo_id, scanner="semgrep", semgrep_rules="p/python")
    row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "running"
    assert row["scanner"] == "semgrep"
    assert row["finished_at"] is None


def test_finish_run_success(db) -> None:
    repo_id = get_or_create_repo(db, "/repo/b")
    run_id = create_run(db, repo_id, scanner="semgrep")
    finish_run(db, run_id, status="success")
    row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "success"
    assert row["finished_at"] is not None


def test_finish_run_error(db) -> None:
    repo_id = get_or_create_repo(db, "/repo/c")
    run_id = create_run(db, repo_id, scanner="semgrep")
    finish_run(db, run_id, status="error", error="semgrep timed out")
    row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "error"
    assert "timed out" in row["error"]


def test_insert_and_query_finding(db) -> None:
    repo_id = get_or_create_repo(db, "/repo/d")
    run_id = create_run(db, repo_id, scanner="semgrep")
    insert_finding(
        db,
        run_id=run_id,
        rule_id="python.lang.security.audit.eval.eval",
        file_path="vulnerable.py",
        line_start=12,
        line_end=12,
        severity="error",
        message="Use of eval detected",
        fingerprint="abc123",
    )
    rows = db.execute("SELECT * FROM findings WHERE run_id = ?", (run_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["rule_id"] == "python.lang.security.audit.eval.eval"
    assert rows[0]["line_start"] == 12


def test_run_always_created_even_before_scanner(db) -> None:
    """Invariant: runs row exists before scanner fires (AC-02 / test contract invariant)."""
    repo_id = get_or_create_repo(db, "/repo/e")
    run_id = create_run(db, repo_id, scanner="semgrep")
    count = db.execute("SELECT COUNT(*) FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
    assert count == 1
