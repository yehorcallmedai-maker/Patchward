# KS-TRACE: AC-02, AC-03, ADR-008 | assumption: SQLite available in stdlib | test: test_db.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER NOT NULL,
    applied_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS repos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id         INTEGER NOT NULL REFERENCES repos(id),
    started_at      TEXT    NOT NULL,
    finished_at     TEXT,
    status          TEXT    NOT NULL DEFAULT 'running',
    scanner         TEXT    NOT NULL,
    semgrep_rules   TEXT,
    error           TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(id),
    rule_id         TEXT    NOT NULL,
    file_path       TEXT    NOT NULL,
    line_start      INTEGER,
    line_end        INTEGER,
    severity        TEXT,
    message         TEXT,
    fingerprint     TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_db(db_path: Path) -> sqlite3.Connection:
    """Open (or create) the SQLite state store and apply schema migrations."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current = row[0] or 0
    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, _now()),
        )
        conn.commit()


def get_or_create_repo(conn: sqlite3.Connection, repo_path: str) -> int:
    row = conn.execute("SELECT id FROM repos WHERE path = ?", (repo_path,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO repos (path, created_at) VALUES (?, ?)",
        (repo_path, _now()),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def create_run(
    conn: sqlite3.Connection,
    repo_id: int,
    scanner: str,
    semgrep_rules: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO runs (repo_id, started_at, scanner, semgrep_rules) VALUES (?, ?, ?, ?)",
        (repo_id, _now(), scanner, semgrep_rules),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    status: str = "success",
    error: str | None = None,
) -> None:
    conn.execute(
        "UPDATE runs SET finished_at = ?, status = ?, error = ? WHERE id = ?",
        (_now(), status, error, run_id),
    )
    conn.commit()


def insert_finding(
    conn: sqlite3.Connection,
    run_id: int,
    rule_id: str,
    file_path: str,
    line_start: int | None,
    line_end: int | None,
    severity: str | None,
    message: str | None,
    fingerprint: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO findings
           (run_id, rule_id, file_path, line_start, line_end, severity, message, fingerprint)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, rule_id, file_path, line_start, line_end, severity, message, fingerprint),
    )
    conn.commit()
