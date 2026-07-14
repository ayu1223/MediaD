from __future__ import annotations

import pytest

from app.database.database import Database


@pytest.fixture
def database(tmp_path):
    db = Database(db_path=tmp_path / "test.db")
    yield db
    db.close()


def test_migration_creates_expected_tables(database):
    tables = {row["name"] for row in database.query("SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert {"history", "app_state"} <= tables


def test_migration_is_idempotent(tmp_path):
    path = tmp_path / "test.db"
    first = Database(db_path=path)
    first.close()

    second = Database(db_path=path)  # should not raise on re-migration
    tables = {row["name"] for row in second.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
    second.close()

    assert {"history", "app_state"} <= tables


def test_execute_persists_data(database):
    database.execute("INSERT INTO app_state (key, value) VALUES (?, ?)", ("k", "v"))

    rows = database.query("SELECT value FROM app_state WHERE key = ?", ("k",))

    assert rows[0]["value"] == "v"


def test_transaction_rolls_back_on_error(database):
    database.execute("INSERT INTO app_state (key, value) VALUES (?, ?)", ("k", "v1"))

    with pytest.raises(RuntimeError):
        with database.transaction() as cursor:
            cursor.execute("UPDATE app_state SET value = ? WHERE key = ?", ("v2", "k"))
            raise RuntimeError("simulated failure")

    rows = database.query("SELECT value FROM app_state WHERE key = ?", ("k",))
    assert rows[0]["value"] == "v1"


def test_transaction_commits_on_success(database):
    with database.transaction() as cursor:
        cursor.execute("INSERT INTO app_state (key, value) VALUES (?, ?)", ("k", "v"))

    rows = database.query("SELECT value FROM app_state WHERE key = ?", ("k",))
    assert rows[0]["value"] == "v"
