"""Issue 7/8: a second, independent YouTube extraction engine.

Two classes live here:

- YouTubeNativeProvider: the actual native engine (InnerTube-based metadata and
  stream-URL extraction, manual HTTP download, ffmpeg muxing). Raises
  NativeExtractionError (see native/exceptions.py) for anything it can't do.

- YouTubeProvider: the Provider actually registered with the DownloaderEngine
  (see engine.py). It is a thin composite/facade: try the native engine first;
  on any NativeExtractionError, log a warning and transparently fall back to a
  YtDlpProvider instance for that same call. This is what satisfies "the
  application should be able to switch internally... no user interaction
  required" — the switch happens per-call, automatically, with yt-dlp as the
  robust, fully-featured safety net for anything the lightweight native path
  can't handle (age-gated videos, cipher-gated formats, malformed playlist
  responses, non-YouTube URLs that happen to reach this far, etc).
"""
from __future__ import annotations

import threading
from pathlib import Path

from app.core.logger import get_logger
from app.downloader.merger import MergeError, merge_streams
from app.downloader.progress import DownloadCancelledError, DownloadPausedError
from app.downloader.providers.base import ProgressCallback, Provider
from app.downloader.providers.ytdlp_provider import YtDlpProvider
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

from .native import youtube_client
from .native.exceptions import NativeExtractionError
from .native.formats import StreamFormat, select_audio_format, select_video_format
from .native.utils import extract_playlist_id, extract_video_id, is_youtube_url

_logger = get_logger(__name__)

_CHUNK_SIZE = 1024 * 64


class YouTubeNativeProvider(Provider):
    """Pure native engine — see module docstring. Not registered directly with
    the DownloaderEngine; used only via YouTubeProvider below."""

    name = "youtube-native"

    def can_handle(self, url: str) -> bool:
        return is_youtube_url(url)

    def extract(self, url: str) -> MediaInfo | PlaylistInfo:
        playlist_id = extract_playlist_id(url)
        if playlist_id:
            return youtube_client.extract_playlist(playlist_id, url)

        video_id = extract_video_id(url)
        if not video_id:
            raise NativeExtractionError(f"Could not find a video or playlist ID in {url}.")
        return youtube_client.extract_video(video_id, url)

    def download(
        self,
        item: DownloadItem,
        progress_cb: ProgressCallback,
        cancel_event: threading.Event,
        pause_event: threading.Event | None = None,
    ) -> None:
        video_id = extract_video_id(item.media_info.source_url)
        if not video_id:
            raise NativeExtractionError(f"Could not find a video ID in {item.media_info.source_url}.")

        formats = youtube_client.get_download_formats(video_id)
        item.destination_path.parent.mkdir(parents=True, exist_ok=True)

        if item.audio_only:
            audio_format = select_audio_format(formats)
            self._download_single_stream(audio_format, item.destination_path, progress_cb, cancel_event, pause_event)
            return

        video_format = select_video_format(formats, item.quality)
        if video_format.is_progressive:
            # A progressive format already contains both audio and video — no
            # muxing needed, just download it directly to the destination.
            self._download_single_stream(video_format, item.destination_path, progress_cb, cancel_event, pause_event)
            return

        audio_format = select_audio_format(formats)
        video_tmp = item.destination_path.with_suffix(f".video.{video_format.container}")
        audio_tmp = item.destination_path.with_suffix(f".audio.{audio_format.container}")
        try:
            # Weight progress ~60/40 between video/audio since video is usually
            # the larger of the two downloads.
            self._download_single_stream(
                video_format, video_tmp, progress_cb, cancel_event, pause_event, weight=(0, 0.6)
            )
            self._download_single_stream(
                audio_format, audio_tmp, progress_cb, cancel_event, pause_event, weight=(0.6, 1.0)
            )
            try:
                merge_streams(video_tmp, audio_tmp, item.destination_path)
            except MergeError as error:
                raise NativeExtractionError(f"Native download succeeded but muxing failed: {error}") from error
        except (DownloadCancelledError, DownloadPausedError):
            # Only clean up on a genuine cancel; a pause preserves partial
            # progress the same way the yt-dlp provider does (Issue 4).
            if not (pause_event is not None and pause_event.is_set()):
                video_tmp.unlink(missing_ok=True)
                audio_tmp.unlink(missing_ok=True)
            raise

    @staticmethod
    def _download_single_stream(
        fmt: StreamFormat,
        destination: Path,
        progress_cb: ProgressCallback,
        cancel_event: threading.Event,
        pause_event: threading.Event | None,
        weight: tuple[float, float] = (0.0, 1.0),
    ) -> None:
        """Stream fmt.url to destination via chunked HTTP GET, honoring
        cancellation and pausing, and resuming from an existing partial file via
        an HTTP Range request exactly like DirectHttpProvider does."""
        import urllib.request

        already_downloaded = destination.stat().st_size if destination.exists() else 0
        headers = {"User-Agent": "MediaDownloader/0.1.0"}
        if already_downloaded:
            headers["Range"] = f"bytes={already_downloaded}-"

        request = urllib.request.Request(fmt.url, headers=headers)
        weight_start, weight_end = weight

        with urllib.request.urlopen(request, timeout=30) as response:
            is_resumed = already_downloaded and response.status == 206
            if already_downloaded and not is_resumed:
                already_downloaded = 0

            content_length = int(response.headers.get("Content-Length", 0))
            total = (already_downloaded + content_length) if content_length else (fmt.filesize_bytes or 0)
            downloaded = already_downloaded
            mode = "ab" if is_resumed else "wb"

            with destination.open(mode) as handle:
                while True:
                    if cancel_event.is_set():
                        raise DownloadCancelledError("Download cancelled by user.")
                    if pause_event is not None and pause_event.is_set():
                        raise DownloadPausedError("Download paused by user.")
                    chunk = response.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        overall_fraction = weight_start + (downloaded / total) * (weight_end - weight_start)
                        progress_cb(int(overall_fraction * total), total, 0.0)
                    else:
                        progress_cb(downloaded, 0, 0.0)


class YouTubeProvider(Provider):
    """Composite provider registered with the DownloaderEngine: native-first,
    automatic transparent fallback to yt-dlp. See module docstring."""

    name = "youtube"

    def __init__(self, ytdlp_provider: YtDlpProvider | None = None) -> None:
        self._native = YouTubeNativeProvider()
        self._ytdlp = ytdlp_provider or YtDlpProvider()

    def set_cookies_file(self, cookies_file: str | None) -> None:
        """Forwarded to the underlying YtDlpProvider fallback; the native engine
        doesn't use cookies (Issue 8: it should keep working anonymously
        wherever YouTube allows it, independent of cookie configuration)."""
        if hasattr(self._ytdlp, "set_cookies_file"):
            self._ytdlp.set_cookies_file(cookies_file)

    def can_handle(self, url: str) -> bool:
        return is_youtube_url(url)

    def extract(self, url: str) -> MediaInfo | PlaylistInfo:
        try:
            return self._native.extract(url)
        except NativeExtractionError as error:
            _logger.info("Native extraction failed for %s (%s); falling back to yt-dlp.", url, error)
            return self._ytdlp.extract(url)

    def download(
        self,
        item: DownloadItem,
        progress_cb: ProgressCallback,
        cancel_event: threading.Event,
        pause_event: threading.Event | None = None,
    ) -> None:
        try:
            self._native.download(item, progress_cb, cancel_event, pause_event)
        except (DownloadCancelledError, DownloadPausedError):
            raise  # user-requested stop, not a native-engine failure — never fall back for this
        except NativeExtractionError as error:
            _logger.info(
                "Native download failed for '%s' (%s); falling back to yt-dlp.", item.media_info.title, error
            )
            self._ytdlp.download(item, progress_cb, cancel_event, pause_event)