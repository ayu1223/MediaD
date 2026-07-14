from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.database.database import Database
from app.database.history_repository import HistoryRepository
from app.models.history_item import HistoryItem, MediaType


@pytest.fixture
def repository(tmp_path):
    db = Database(db_path=tmp_path / "test.db")
    yield HistoryRepository(db)
    db.close()


def _make_item(item_id: str, title: str) -> HistoryItem:
    return HistoryItem(
        id=item_id,
        title=title,
        provider="yt-dlp",
        source_url=f"https://example.com/{item_id}",
        file_path=Path(f"/downloads/{title}.mp4"),
        media_type=MediaType.VIDEO,
        quality="1080p",
        file_size_bytes=1024,
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        thumbnail_url=None,
    )


def test_add_and_get_by_id(repository):
    item = _make_item("1", "Video One")

    repository.add(item)
    fetched = repository.get_by_id("1")

    assert fetched is not None
    assert fetched.title == "Video One"
    assert fetched.file_path == Path("/downloads/Video One.mp4")
    assert fetched.media_type == MediaType.VIDEO


def test_add_replaces_existing_record_with_same_id(repository):
    repository.add(_make_item("1", "Original"))
    repository.add(_make_item("1", "Replaced"))

    all_items = repository.get_all()

    assert len(all_items) == 1
    assert all_items[0].title == "Replaced"


def test_get_by_id_returns_none_when_missing(repository):
    assert repository.get_by_id("missing") is None


def test_get_all_orders_by_completed_at_descending(repository):
    older = _make_item("1", "Older")
    older.completed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = _make_item("2", "Newer")
    newer.completed_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    repository.add(older)
    repository.add(newer)

    result = repository.get_all()

    assert [item.title for item in result] == ["Newer", "Older"]


def test_search_matches_partial_title_case_insensitively(repository):
    repository.add(_make_item("1", "Funny Cat Video"))
    repository.add(_make_item("2", "Serious Documentary"))

    result = repository.search("cat")

    assert [item.title for item in result] == ["Funny Cat Video"]


def test_delete_removes_single_record(repository):
    repository.add(_make_item("1", "Video"))

    repository.delete("1")

    assert repository.get_all() == []


def test_clear_removes_all_records(repository):
    repository.add(_make_item("1", "A"))
    repository.add(_make_item("2", "B"))

    repository.clear()

    assert repository.get_all() == []
