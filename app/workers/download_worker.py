from __future__ import annotations

import threading
from collections.abc import Callable

from PySide6.QtCore import QThread, Signal

from app.core.logger import get_logger
from app.models.download_item import DownloadItem, DownloadStatus

_logger = get_logger(__name__)

ProgressCallback = Callable[[int, int, float], None]
DownloadFunction = Callable[[DownloadItem, ProgressCallback, threading.Event], None]


class DownloadWorker(QThread):
    """Runs a download callable off the UI thread, reporting progress and completion via signals."""

    progress = Signal(object)
    finished_ok = Signal(object)
    failed = Signal(object, str)

    def __init__(self, item: DownloadItem, download_fn: DownloadFunction, parent=None) -> None:
        super().__init__(parent)
        self._item = item
        self._download_fn = download_fn
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request cooperative cancellation; the injected download function must honor cancel_event."""
        self._cancel_event.set()

    def _on_progress(self, downloaded_bytes: int, total_bytes: int, speed_bytes_per_sec: float) -> None:
        self._item.downloaded_bytes = downloaded_bytes
        self._item.total_bytes = total_bytes
        self._item.speed_bytes_per_sec = speed_bytes_per_sec
        self._item.progress_percent = (downloaded_bytes / total_bytes * 100) if total_bytes else 0.0
        self.progress.emit(self._item)

    def run(self) -> None:
        self._item.status = DownloadStatus.DOWNLOADING
        try:
            self._download_fn(self._item, self._on_progress, self._cancel_event)
        except Exception as error:  # noqa: BLE001 - worker boundary must not crash the thread
            if self._cancel_event.is_set():
                self._item.status = DownloadStatus.CANCELLED
                _logger.info("Download cancelled for %s", self._item.media_info.title)
                self.finished_ok.emit(self._item)
                return
            self._item.status = DownloadStatus.FAILED
            self._item.error_message = str(error)
            _logger.error("Download failed for %s: %s", self._item.media_info.title, error)
            self.failed.emit(self._item, str(error))
            return

        if self._cancel_event.is_set():
            self._item.status = DownloadStatus.CANCELLED
        else:
            self._item.status = DownloadStatus.COMPLETED
            self._item.progress_percent = 100.0
        self.finished_ok.emit(self._item)
