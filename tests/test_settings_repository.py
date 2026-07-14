from __future__ import annotations

import pytest

from app.database.database import Database
from app.database.settings_repository import SettingsRepository


@pytest.fixture
def repository(tmp_path):
    db = Database(db_path=tmp_path / "test.db")
    yield SettingsRepository(db)
    db.close()


def test_get_returns_default_when_missing(repository):
    assert repository.get("missing", default="fallback") == "fallback"


def test_set_and_get_round_trip(repository):
    repository.set("key", "value")

    assert repository.get("key") == "value"


def test_set_overwrites_existing_value(repository):
    repository.set("key", "first")
    repository.set("key", "second")

    assert repository.get("key") == "second"


def test_delete_removes_key(repository):
    repository.set("key", "value")

    repository.delete("key")

    assert repository.get("key") is None


def test_get_all_returns_every_pair(repository):
    repository.set("a", "1")
    repository.set("b", "2")

    assert repository.get_all() == {"a": "1", "b": "2"}
