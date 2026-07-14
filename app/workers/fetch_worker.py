from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QThread, Signal

from app.core.logger import get_logger
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

_logger = get_logger(__name__)

FetchFunction = Callable[[str], "MediaInfo | PlaylistInfo"]


class FetchWorker(QThread):
    """Runs a metadata-fetching callable off the UI thread and reports the result via signals."""

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, url: str, fetch_fn: FetchFunction, parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._fetch_fn = fetch_fn

    def run(self) -> None:
        try:
            result = self._fetch_fn(self._url)
        except Exception as error:  # noqa: BLE001 - worker boundary must not crash the thread
            _logger.error("Fetch failed for %s: %s", self._url, error)
            self.failed.emit(str(error))
            return
        self.finished_ok.emit(result)
