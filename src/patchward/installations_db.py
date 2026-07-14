# KS-TRACE: P1-WEBHOOK-02 | assumption: SQLite is sufficient for v0
# install/billing-state volume (see ADR-030 in
# memory/architectural_decisions.md — narrow v0 before a
# managed Postgres migration) | test: test_installations_db.py
"""
Persistence for GitHub App installations, their installed repos, and
Marketplace purchase state.

Mirrors the style of db.py (stdlib sqlite3, explicit DDL, a bumped
SCHEMA_VERSION for migrations) rather than introducing a new ORM or
a Postgres dependency for the first version of the webhook service.
Swapping this module out for a Postgres-backed one later (once install
volume justifies it — see ADR-030 in memory/architectural_decisions.md)
should not require changing webhook.py's call sites, only this file's
internals.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER NOT NULL,
    applied_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS installations (
    id              INTEGER PRIMARY KEY,  -- GitHub installation id, not autoincrement
    account_login   TEXT    NOT NULL,
    account_type    TEXT    NOT NULL,      -- 'Organization' | 'User'
    installed_at    TEXT    NOT NULL,
    suspended_at    TEXT
);

CREATE TABLE IF NOT EXISTS installation_repos (
    installation_id INTEGER NOT NULL REFERENCES installations(id),
    repo_full_name  TEXT    NOT NULL,      -- e.g. "acme/backend"
    added_at        TEXT    NOT NULL,
    removed_at      TEXT,
    PRIMARY KEY (installation_id, repo_full_name)
);

CREATE TABLE IF NOT EXISTS marketplace_purchases (
    account_login   TEXT    NOT NULL,
    plan_id         INTEGER NOT NULL,
    unit_count      INTEGER NOT NULL DEFAULT 1,
    billing_cycle   TEXT,
    status          TEXT    NOT NULL,      -- purchased | changed | cancelled | pending_change
    effective_date  TEXT    NOT NULL,
    PRIMARY KEY (account_login)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_db(db_path: Path) -> sqlite3.Connection:
    """Open (or create) the installations state store and apply migrations."""
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


def upsert_installation(
    conn: sqlite3.Connection,
    installation_id: int,
    account_login: str,
    account_type: str,
) -> None:
    conn.execute(
        """INSERT INTO installations (id, account_login, account_type, installed_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             account_login = excluded.account_login,
             account_type  = excluded.account_type,
             suspended_at  = NULL""",
        (installation_id, account_login, account_type, _now()),
    )
    conn.commit()


def mark_installation_suspended(conn: sqlite3.Connection, installation_id: int) -> None:
    conn.execute(
        "UPDATE installations SET suspended_at = ? WHERE id = ?",
        (_now(), installation_id),
    )
    conn.commit()


def mark_installation_unsuspended(conn: sqlite3.Connection, installation_id: int) -> None:
    conn.execute(
        "UPDATE installations SET suspended_at = NULL WHERE id = ?",
        (installation_id,),
    )
    conn.commit()


def delete_installation(conn: sqlite3.Connection, installation_id: int) -> None:
    conn.execute("DELETE FROM installation_repos WHERE installation_id = ?", (installation_id,))
    conn.execute("DELETE FROM installations WHERE id = ?", (installation_id,))
    conn.commit()


def add_installation_repo(
    conn: sqlite3.Connection, installation_id: int, repo_full_name: str
) -> None:
    conn.execute(
        """INSERT INTO installation_repos (installation_id, repo_full_name, added_at)
           VALUES (?, ?, ?)
           ON CONFLICT(installation_id, repo_full_name) DO UPDATE SET removed_at = NULL""",
        (installation_id, repo_full_name, _now()),
    )
    conn.commit()


def remove_installation_repo(
    conn: sqlite3.Connection, installation_id: int, repo_full_name: str
) -> None:
    conn.execute(
        "UPDATE installation_repos SET removed_at = ? WHERE installation_id = ? AND repo_full_name = ?",
        (_now(), installation_id, repo_full_name),
    )
    conn.commit()


def list_active_repos(conn: sqlite3.Connection, installation_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT repo_full_name FROM installation_repos WHERE installation_id = ? AND removed_at IS NULL",
        (installation_id,),
    ).fetchall()
    return [row["repo_full_name"] for row in rows]


def upsert_marketplace_purchase(
    conn: sqlite3.Connection,
    account_login: str,
    plan_id: int,
    unit_count: int,
    billing_cycle: str | None,
    status: str,
) -> None:
    conn.execute(
        """INSERT INTO marketplace_purchases
             (account_login, plan_id, unit_count, billing_cycle, status, effective_date)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(account_login) DO UPDATE SET
             plan_id        = excluded.plan_id,
             unit_count     = excluded.unit_count,
             billing_cycle  = excluded.billing_cycle,
             status         = excluded.status,
             effective_date = excluded.effective_date""",
        (account_login, plan_id, unit_count, billing_cycle, status, _now()),
    )
    conn.commit()


def is_entitled(conn: sqlite3.Connection, account_login: str) -> bool:
    """
    Return True if account_login has an active (non-cancelled)
    Marketplace purchase on file. Used to gate scan runs — see
    webhook.py's trigger_scan_for_installation.
    """
    row = conn.execute(
        "SELECT status FROM marketplace_purchases WHERE account_login = ?",
        (account_login,),
    ).fetchone()
    return bool(row) and row["status"] != "cancelled"
