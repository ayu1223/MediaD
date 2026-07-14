from __future__ import annotations

import threading
from urllib.parse import urlparse

from app.core.logger import get_logger
from app.downloader.progress import DownloadCancelledError
from app.downloader.providers.base import ProgressCallback, Provider
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo

_logger = get_logger(__name__)

_DIRECT_EXTENSIONS = (".mp4", ".mp3", ".m4a", ".webm", ".mkv", ".wav", ".flac", ".mov")
_CHUNK_SIZE = 1024 * 64


class DirectHttpProvider(Provider):
    """Provider for URLs that point directly at a downloadable media file."""

    name = "direct"

    def can_handle(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return path.endswith(_DIRECT_EXTENSIONS)

    def extract(self, url: str) -> MediaInfo:
        path = urlparse(url).path
        filename = path.rsplit("/", 1)[-1] or "download"
        extension = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        return MediaInfo(
            id=filename,
            title=filename,
            provider=self.name,
            source_url=url,
            available_qualities=["original"],
            available_audio_formats=[],
            extra={"extension": extension},
        )

    def download(self, item: DownloadItem, progress_cb: ProgressCallback, cancel_event: threading.Event) -> None:
        import urllib.request

        request = urllib.request.Request(item.media_info.source_url, headers={"User-Agent": "MediaDownloader/0.1.0"})
        item.destination_path.parent.mkdir(parents=True, exist_ok=True)

        with urllib.request.urlopen(request, timeout=30) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with item.destination_path.open("wb") as handle:
                while True:
                    if cancel_event.is_set():
                        raise DownloadCancelledError("Download cancelled by user.")
                    chunk = response.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    progress_cb(downloaded, total, 0.0)
