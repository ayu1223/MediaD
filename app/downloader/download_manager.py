from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.core.logger import get_logger
from app.downloader.engine import DownloaderEngine
from app.downloader.queue_manager import QueueManager
from app.models.download_item import DownloadItem, DownloadStatus
from app.models.media_info import MediaInfo
from app.workers.download_worker import DownloadWorker

_logger = get_logger(__name__)


class DownloadManager(QObject):
    """Coordinates queued downloads: schedules workers up to max_concurrent and relays their signals."""

    progress = Signal(object)
    item_started = Signal(object)
    item_completed = Signal(object)
    item_cancelled = Signal(object)
    item_failed = Signal(object, str)
    queue_changed = Signal()

    def __init__(self, engine: DownloaderEngine, queue_manager: QueueManager, max_concurrent: int = 3) -> None:
        super().__init__()
        self._engine = engine
        self._queue = queue_manager
        self._max_concurrent = max_concurrent
        self._active_workers: dict[str, DownloadWorker] = {}

    def set_max_concurrent(self, value: int) -> None:
        self._max_concurrent = max(1, value)
        self._maybe_start_next()

    def enqueue(
        self,
        media_info: MediaInfo,
        destination_path: Path,
        quality: str,
        audio_only: bool = False,
        audio_format: str | None = None,
    ) -> DownloadItem:
        item = DownloadItem(
            media_info=media_info,
            destination_path=destination_path,
            quality=quality,
            audio_only=audio_only,
            audio_format=audio_format,
        )
        self._queue.add(item)
        self.queue_changed.emit()
        self._maybe_start_next()
        return item

    def cancel(self, item_id: str) -> None:
        worker = self._active_workers.get(item_id)
        if worker is not None:
            worker.cancel()
            return
        item = self._queue.get(item_id)
        if item is not None and item.status == DownloadStatus.QUEUED:
            item.status = DownloadStatus.CANCELLED
            self._queue.notify_changed(item)
            self.item_cancelled.emit(item)
            self.queue_changed.emit()

    def active_count(self) -> int:
        return len(self._active_workers)

    def clear_finished(self) -> None:
        """Remove every item in a terminal state (completed/failed/cancelled) from
        the queue. Active/queued items are left untouched. Task 6: makes the
        Downloads page's "Clear completed" button an actual operation instead of
        a documented no-op."""
        finished_ids = [item.id for item in self._queue.list_all() if item.is_finished()]
        for item_id in finished_ids:
            self._queue.remove(item_id)
        if finished_ids:
            self.queue_changed.emit()

    def _maybe_start_next(self) -> None:
        while len(self._active_workers) < self._max_concurrent:
            item = self._queue.pop_next_pending()
            if item is None:
                break
            self._start_worker(item)

    def _start_worker(self, item: DownloadItem) -> None:
        item.status = DownloadStatus.DOWNLOADING
        self._queue.notify_changed(item)
        provider = self._engine.find_provider(item.media_info.source_url)
        worker = DownloadWorker(item, download_fn=provider.download, parent=self)
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(worker.deleteLater)
        self._active_workers[item.id] = worker
        _logger.info("Starting download: %s", item.media_info.title)
        worker.start()
        self.item_started.emit(item)

    def _on_progress(self, item: DownloadItem) -> None:
        self._queue.notify_changed(item)
        self.progress.emit(item)

    def _on_finished(self, item: DownloadItem) -> None:
        self._active_workers.pop(item.id, None)
        self._queue.notify_changed(item)
        if item.status == DownloadStatus.COMPLETED:
            self.item_completed.emit(item)
        elif item.status == DownloadStatus.CANCELLED:
            # Task 5/6: cancellation previously produced no notification at all —
            # finished_ok fires for both a completed and a cancelled item, but
            # only COMPLETED was ever surfaced to the UI.
            self.item_cancelled.emit(item)
        self._maybe_start_next()

    def _on_failed(self, item: DownloadItem, message: str) -> None:
        self._active_workers.pop(item.id, None)
        self._queue.notify_changed(item)
        self.item_failed.emit(item, message)
        self._maybe_start_next()
