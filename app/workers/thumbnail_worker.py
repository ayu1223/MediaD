from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.logger import get_logger
from app.services.thumbnail_service import ThumbnailService

_logger = get_logger(__name__)


class ThumbnailWorker(QThread):
    """Fetches a single thumbnail off the UI thread using ThumbnailService."""

    finished_ok = Signal(str, object)

    def __init__(self, url: str, thumbnail_service: ThumbnailService, parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._thumbnail_service = thumbnail_service

    def run(self) -> None:
        path = self._thumbnail_service.fetch(self._url)
        if path is None:
            _logger.warning("Thumbnail fetch returned no result for %s", self._url)
        self.finished_ok.emit(self._url, path)
