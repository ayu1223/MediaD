from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable

from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

ProgressCallback = Callable[[int, int, float], None]


class Provider(ABC):
    """A media source capable of extracting metadata and performing downloads for URLs it supports.

    New providers are added by subclassing Provider and registering an instance with
    DownloaderEngine — no other layer needs to change.
    """

    name: str

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this provider can extract metadata and download from the given URL."""

    @abstractmethod
    def extract(self, url: str) -> MediaInfo | PlaylistInfo:
        """Extract metadata for a single item or playlist without downloading it."""

    @abstractmethod
    def download(self, item: DownloadItem, progress_cb: ProgressCallback, cancel_event: threading.Event) -> None:
        """Perform the download described by item, reporting progress via progress_cb.

        Must periodically check cancel_event and stop promptly when it is set.
        Must write the final file to item.destination_path.
        """
