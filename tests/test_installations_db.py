# KS-TRACE: P1-WEBHOOK-02 | test: installation/repo/purchase state CRUD
from __future__ import annotations

from pathlib import Path

import pytest

from patchward.installations_db import (
    SCHEMA_VERSION,
    add_installation_repo,
    delete_installation,
    is_entitled,
    list_active_repos,
    mark_installation_suspended,
    mark_installation_unsuspended,
    open_db,
    remove_installation_repo,
    upsert_installation,
    upsert_marketplace_purchase,
)


@pytest.fixture()
def db(tmp_path: Path):
    conn = open_db(tmp_path / "webhook_state.db")
    yield conn
    conn.close()


def test_schema_version_written(db) -> None:
    row = db.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
    assert row["v"] == SCHEMA_VERSION


def test_upsert_installation_idempotent(db) -> None:
    upsert_installation(db, 111, "acme", "Organization")
    upsert_installation(db, 111, "acme", "Organization")
    row = db.execute("SELECT * FROM installations WHERE id = ?", (111,)).fetchone()
    assert row["account_login"] == "acme"
    assert row["account_type"] == "Organization"
    assert row["suspended_at"] is None


def test_suspend_then_unsuspend_clears_field(db) -> None:
    upsert_installation(db, 222, "acme", "Organization")
    mark_installation_suspended(db, 222)
    row = db.execute("SELECT suspended_at FROM installations WHERE id = ?", (222,)).fetchone()
    assert row["suspended_at"] is not None

    mark_installation_unsuspended(db, 222)
    row = db.execute("SELECT suspended_at FROM installations WHERE id = ?", (222,)).fetchone()
    assert row["suspended_at"] is None


def test_delete_installation_removes_repos_too(db) -> None:
    upsert_installation(db, 333, "acme", "Organization")
    add_installation_repo(db, 333, "acme/backend")
    delete_installation(db, 333)

    assert db.execute("SELECT * FROM installations WHERE id = ?", (333,)).fetchone() is None
    assert (
        db.execute(
            "SELECT * FROM installation_repos WHERE installation_id = ?", (333,)
        ).fetchone()
        is None
    )


def test_add_and_remove_repo_reflected_in_active_list(db) -> None:
    upsert_installation(db, 444, "acme", "Organization")
    add_installation_repo(db, 444, "acme/backend")
    add_installation_repo(db, 444, "acme/frontend")
    assert set(list_active_repos(db, 444)) == {"acme/backend", "acme/frontend"}

    remove_installation_repo(db, 444, "acme/frontend")
    assert list_active_repos(db, 444) == ["acme/backend"]


def test_re_adding_a_removed_repo_clears_removed_at(db) -> None:
    upsert_installation(db, 555, "acme", "Organization")
    add_installation_repo(db, 555, "acme/backend")
    remove_installation_repo(db, 555, "acme/backend")
    assert list_active_repos(db, 555) == []

    add_installation_repo(db, 555, "acme/backend")
    assert list_active_repos(db, 555) == ["acme/backend"]


def test_is_entitled_false_with_no_purchase_on_file(db) -> None:
    assert is_entitled(db, "acme") is False


def test_is_entitled_true_after_purchase(db) -> None:
    upsert_marketplace_purchase(
        db, account_login="acme", plan_id=1, unit_count=5,
        billing_cycle="monthly", status="purchased",
    )
    assert is_entitled(db, "acme") is True


def test_is_entitled_false_after_cancellation(db) -> None:
    upsert_marketplace_purchase(
        db, account_login="acme", plan_id=1, unit_count=5,
        billing_cycle="monthly", status="purchased",
    )
    upsert_marketplace_purchase(
        db, account_login="acme", plan_id=1, unit_count=5,
        billing_cycle="monthly", status="cancelled",
    )
    assert is_entitled(db, "acme") is False


def test_upsert_purchase_updates_unit_count_on_plan_change(db) -> None:
    upsert_marketplace_purchase(
        db, account_login="acme", plan_id=1, unit_count=5,
        billing_cycle="monthly", status="purchased",
    )
    upsert_marketplace_purchase(
        db, account_login="acme", plan_id=1, unit_count=12,
        billing_cycle="monthly", status="changed",
    )
    row = db.execute(
        "SELECT unit_count, status FROM marketplace_purchases WHERE account_login = ?",
        ("acme",),
    ).fetchone()
    assert row["unit_count"] == 12
    assert row["status"] == "changed"
