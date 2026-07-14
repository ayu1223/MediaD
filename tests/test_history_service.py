from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.database.database import Database
from app.database.history_repository import HistoryRepository
from app.models.history_item import HistoryItem, MediaType
from app.services.history_service import HistoryService


@pytest.fixture
def service(tmp_path):
    db = Database(db_path=tmp_path / "test.db")
    yield HistoryService(HistoryRepository(db))
    db.close()


def _item(item_id: str, title: str) -> HistoryItem:
    return HistoryItem(
        id=item_id,
        title=title,
        provider="yt-dlp",
        source_url="https://example.com",
        file_path=Path("/downloads/x.mp4"),
        media_type=MediaType.VIDEO,
        quality="1080p",
        file_size_bytes=100,
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_add_then_list_all(service):
    service.add(_item("1", "Video"))

    assert [item.title for item in service.list_all()] == ["Video"]


def test_search_with_blank_query_returns_all(service):
    service.add(_item("1", "Video"))

    assert service.search("   ") == service.list_all()


def test_search_delegates_to_repository_search(service):
    service.add(_item("1", "Cat Video"))
    service.add(_item("2", "Dog Video"))

    assert [item.title for item in service.search("Cat")] == ["Cat Video"]


def test_delete_removes_single_item(service):
    service.add(_item("1", "Video"))

    service.delete("1")

    assert service.list_all() == []


def test_clear_removes_everything(service):
    service.add(_item("1", "A"))
    service.add(_item("2", "B"))

    service.clear()

    assert service.list_all() == []
