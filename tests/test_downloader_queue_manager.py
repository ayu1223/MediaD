from __future__ import annotations

from pathlib import Path

from app.downloader.queue_manager import QueueManager
from app.models.download_item import DownloadItem, DownloadStatus
from app.models.media_info import MediaInfo


def _make_item(title: str = "Video") -> DownloadItem:
    media = MediaInfo(id=title, title=title, provider="test", source_url="https://example.com")
    return DownloadItem(media_info=media, destination_path=Path("/tmp") / f"{title}.mp4", quality="720p")


def test_add_appends_and_emits_item_added():
    manager = QueueManager()
    received = []
    manager.item_added.connect(received.append)
    item = _make_item()

    manager.add(item)

    assert manager.list_all() == [item]
    assert received == [item]


def test_get_returns_none_for_unknown_id():
    manager = QueueManager()

    assert manager.get("missing") is None


def test_remove_deletes_item_and_emits_item_removed():
    manager = QueueManager()
    item = _make_item()
    manager.add(item)
    received = []
    manager.item_removed.connect(received.append)

    manager.remove(item.id)

    assert manager.list_all() == []
    assert received == [item.id]


def test_remove_unknown_id_is_a_no_op():
    manager = QueueManager()

    manager.remove("missing")  # should not raise

    assert manager.list_all() == []


def test_list_pending_only_returns_queued_items():
    manager = QueueManager()
    queued = _make_item("queued")
    active = _make_item("active")
    active.status = DownloadStatus.DOWNLOADING
    manager.add(queued)
    manager.add(active)

    assert manager.list_pending() == [queued]


def test_pop_next_pending_returns_first_queued_without_removing():
    manager = QueueManager()
    first = _make_item("first")
    second = _make_item("second")
    manager.add(first)
    manager.add(second)

    result = manager.pop_next_pending()

    assert result is first
    assert manager.list_all() == [first, second]


def test_pop_next_pending_returns_none_when_all_active():
    manager = QueueManager()
    item = _make_item()
    item.status = DownloadStatus.DOWNLOADING
    manager.add(item)

    assert manager.pop_next_pending() is None


def test_notify_changed_emits_item_changed():
    manager = QueueManager()
    item = _make_item()
    manager.add(item)
    received = []
    manager.item_changed.connect(received.append)

    manager.notify_changed(item)

    assert received == [item]


def test_maintains_insertion_order():
    manager = QueueManager()
    items = [_make_item(f"item-{i}") for i in range(5)]
    for item in items:
        manager.add(item)

    assert manager.list_all() == items
