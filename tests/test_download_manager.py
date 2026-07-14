from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.downloader import download_manager as download_manager_module
from app.downloader.download_manager import DownloadManager
from app.downloader.engine import DownloaderEngine
from app.downloader.providers.base import Provider
from app.downloader.queue_manager import QueueManager
from app.models.download_item import DownloadStatus
from app.models.media_info import MediaInfo


class _FakeWorker(QObject):
    """Stands in for DownloadWorker: never actually runs a thread, driven manually by tests."""

    progress = Signal(object)
    finished_ok = Signal(object)
    failed = Signal(object, str)
    finished = Signal()

    instances: list["_FakeWorker"] = []

    def __init__(self, item, download_fn, parent=None) -> None:
        super().__init__(parent)
        self.item = item
        self.started = False
        _FakeWorker.instances.append(self)

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.item.status = DownloadStatus.CANCELLED


class _NoopProvider(Provider):
    name = "noop"

    def can_handle(self, url: str) -> bool:
        return True

    def extract(self, url: str):
        raise NotImplementedError

    def download(self, item, progress_cb, cancel_event) -> None:
        raise NotImplementedError


def _media(title: str) -> MediaInfo:
    return MediaInfo(id=title, title=title, provider="noop", source_url="https://example.com")


def _setup(monkeypatch, max_concurrent=1):
    _FakeWorker.instances.clear()
    monkeypatch.setattr(download_manager_module, "DownloadWorker", _FakeWorker)
    engine = DownloaderEngine(providers=[_NoopProvider()])
    queue = QueueManager()
    manager = DownloadManager(engine, queue, max_concurrent=max_concurrent)
    return manager, queue


def test_enqueue_starts_worker_immediately_when_under_limit(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=2)

    item = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")

    assert item.status == DownloadStatus.DOWNLOADING
    assert manager.active_count() == 1
    assert _FakeWorker.instances[0].started is True


def test_enqueue_beyond_limit_stays_queued(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)

    first = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")
    second = manager.enqueue(_media("b"), Path("/tmp/b.mp4"), "720p")

    assert first.status == DownloadStatus.DOWNLOADING
    assert second.status == DownloadStatus.QUEUED
    assert manager.active_count() == 1


def test_completed_worker_frees_slot_for_next_queued_item(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    first = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")
    second = manager.enqueue(_media("b"), Path("/tmp/b.mp4"), "720p")
    worker = _FakeWorker.instances[0]

    first.status = DownloadStatus.COMPLETED
    worker.finished_ok.emit(first)

    assert manager.active_count() == 1
    assert second.status == DownloadStatus.DOWNLOADING


def test_item_completed_signal_emitted_on_success(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    received = []
    manager.item_completed.connect(received.append)
    item = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")
    item.status = DownloadStatus.COMPLETED

    _FakeWorker.instances[0].finished_ok.emit(item)

    assert received == [item]


def test_item_failed_signal_frees_slot_and_notifies(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    received = []
    manager.item_failed.connect(lambda item, message: received.append((item, message)))
    item = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")

    _FakeWorker.instances[0].failed.emit(item, "network error")

    assert received == [(item, "network error")]
    assert manager.active_count() == 0


def test_cancel_active_download_delegates_to_worker(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    item = manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")

    manager.cancel(item.id)

    assert item.status == DownloadStatus.CANCELLED


def test_cancel_queued_download_marks_cancelled_without_worker(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")
    second = manager.enqueue(_media("b"), Path("/tmp/b.mp4"), "720p")

    manager.cancel(second.id)

    assert second.status == DownloadStatus.CANCELLED


def test_set_max_concurrent_starts_additional_queued_items(monkeypatch):
    manager, _queue = _setup(monkeypatch, max_concurrent=1)
    manager.enqueue(_media("a"), Path("/tmp/a.mp4"), "720p")
    second = manager.enqueue(_media("b"), Path("/tmp/b.mp4"), "720p")
    assert second.status == DownloadStatus.QUEUED

    manager.set_max_concurrent(2)

    assert second.status == DownloadStatus.DOWNLOADING
    assert manager.active_count() == 2
