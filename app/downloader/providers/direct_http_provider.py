from __future__ import annotations

import threading
from urllib.parse import urlparse

from app.core.logger import get_logger
from app.downloader.progress import DownloadCancelledError, DownloadPausedError
from app.downloader.providers.base import ProgressCallback, Provider
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo

_logger = get_logger(__name__)

_DIRECT_EXTENSIONS = (".mp4", ".mp3", ".m4a", ".webm", ".mkv", ".wav", ".flac", ".mov")
_CHUNK_SIZE = 1024 * 64


class DirectHttpProvider(Provider):
    """Provider for URLs that point directly at a downloadable media file.

    Supports real pause/resume via HTTP Range requests: pausing simply stops
    writing to the partially-downloaded file (left on disk); resuming re-invokes
    download() for the same item, which detects the existing partial file and
    requests only the remaining bytes with a Range header, appending to it.
    """

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

    def download(
        self,
        item: DownloadItem,
        progress_cb: ProgressCallback,
        cancel_event: threading.Event,
        pause_event: threading.Event | None = None,
    ) -> None:
        import urllib.request

        item.destination_path.parent.mkdir(parents=True, exist_ok=True)

        # Issue 4: resume support. If a previous attempt left a partial file behind
        # (from a pause, or any other interruption), continue from its current
        # size via a Range request and append, instead of restarting from zero.
        already_downloaded = item.destination_path.stat().st_size if item.destination_path.exists() else 0

        headers = {"User-Agent": "MediaDownloader/0.1.0"}
        if already_downloaded:
            headers["Range"] = f"bytes={already_downloaded}-"

        request = urllib.request.Request(item.media_info.source_url, headers=headers)

        with urllib.request.urlopen(request, timeout=30) as response:
            is_resumed = already_downloaded and response.status == 206
            if already_downloaded and not is_resumed:
                # Server doesn't support Range requests (or the resource changed) —
                # fall back to a full restart rather than corrupting the file by
                # appending a full response on top of existing bytes.
                _logger.warning(
                    "Server did not honor Range resume for %s; restarting from scratch.",
                    item.media_info.title,
                )
                already_downloaded = 0

            content_length = int(response.headers.get("Content-Length", 0))
            total = already_downloaded + content_length if content_length else 0
            downloaded = already_downloaded
            mode = "ab" if is_resumed else "wb"

            with item.destination_path.open(mode) as handle:
                while True:
                    if cancel_event.is_set():
                        raise DownloadCancelledError("Download cancelled by user.")
                    if pause_event is not None and pause_event.is_set():
                        # Leave the file exactly as-is (flushed by the `with` block's
                        # close on the way out) so a future resume can Range-continue.
                        raise DownloadPausedError("Download paused by user.")
                    chunk = response.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    progress_cb(downloaded, total, 0.0)