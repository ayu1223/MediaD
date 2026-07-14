from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.core.logger import get_logger
from app.downloader.download_manager import DownloadManager
from app.downloader.engine import DownloaderEngine
from app.downloader.metadata import MetadataExtractor
from app.downloader.queue_manager import QueueManager
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo
from app.services.file_service import FileService
from app.workers.fetch_worker import FetchWorker

_logger = get_logger(__name__)


class DownloadService(QObject):
    """The sole boundary the UI uses to fetch metadata and manage downloads.

    Wraps MetadataExtractor, DownloadManager, and QueueManager so the UI never touches
    the downloader package or any worker directly, per the mandated UI -> Services ->
    Downloader -> Workers architecture.
    """

    metadata_ready = Signal(object)
    metadata_failed = Signal(str)
    progress = Signal(object)
    item_started = Signal(object)
    item_completed = Signal(object)
    item_cancelled = Signal(object)
    item_failed = Signal(object, str)
    queue_changed = Signal()

    def __init__(self, max_concurrent_downloads: int = 3, cookies_file: str | None = None) -> None:
        super().__init__()
        self._engine = DownloaderEngine(cookies_file=cookies_file)
        self._metadata_extractor = MetadataExtractor(self._engine)
        self._queue_manager = QueueManager()
        self._download_manager = DownloadManager(self._engine, self._queue_manager, max_concurrent_downloads)

        self._download_manager.progress.connect(self.progress)
        self._download_manager.item_started.connect(self.item_started)
        self._download_manager.item_completed.connect(self.item_completed)
        self._download_manager.item_cancelled.connect(self.item_cancelled)
        self._download_manager.item_failed.connect(self.item_failed)
        self._download_manager.queue_changed.connect(self.queue_changed)

        self._active_fetch_worker: FetchWorker | None = None
        self._file_service = FileService()

    def fetch_metadata(self, url: str) -> None:
        """Asynchronously resolve a URL to MediaInfo or PlaylistInfo; result arrives via signals."""
        worker = FetchWorker(url, fetch_fn=self._metadata_extractor.extract, parent=self)
        worker.finished_ok.connect(self.metadata_ready)
        worker.failed.connect(self.metadata_failed)
        worker.finished.connect(worker.deleteLater)
        self._active_fetch_worker = worker
        worker.start()

    def enqueue_download(
        self,
        media_info: MediaInfo,
        destination_path: Path,
        quality: str,
        audio_only: bool = False,
        audio_format: str | None = None,
    ) -> DownloadItem:
        return self._download_manager.enqueue(media_info, destination_path, quality, audio_only, audio_format)

    def enqueue_playlist(
        self,
        playlist: PlaylistInfo,
        destination_dir: Path,
        quality: str,
        audio_only: bool = False,
        audio_format: str | None = None,
    ) -> list[DownloadItem]:
        extension = "mp3" if audio_only else "mkv"
        return [
            self.enqueue_download(
                entry,
                self._file_service.build_destination_path(destination_dir, entry.title, extension),
                quality,
                audio_only,
                audio_format,
            )
            for entry in playlist.entries
        ]

    def cancel_download(self, item_id: str) -> None:
        self._download_manager.cancel(item_id)

    def clear_finished(self) -> None:
        """Remove completed/failed/cancelled items from the queue view."""
        self._download_manager.clear_finished()

    def set_max_concurrent_downloads(self, value: int) -> None:
        self._download_manager.set_max_concurrent(value)

    def set_cookies_file(self, cookies_file: str | None) -> None:
        """Update the cookies.txt path used for future metadata/download requests."""
        self._engine.set_cookies_file(cookies_file)
        self._metadata_extractor.invalidate()  # stale metadata may have been cached pre-cookie-fix

    def list_queue(self) -> list[DownloadItem]:
        return self._queue_manager.list_all()
