from __future__ import annotations

import threading
import time

from app.core.logger import get_logger
from app.downloader.engine import DownloaderEngine
from app.downloader.validators import validate_or_raise
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

_logger = get_logger(__name__)

# Issue 3/6: re-fetching the same URL's metadata (title, formats, thumbnail,
# playlist entries, duration) triggers a brand new yt-dlp subprocess every time,
# which is both wasteful and one more request that can trip YouTube's bot
# detection. A short TTL cache means the same URL fetched twice in quick
# succession (e.g. a duplicate click, or a widget that re-reads metadata the
# user already fetched a moment ago) reuses the first result instead of shelling
# out to yt-dlp again. The TTL is intentionally short: this is about eliminating
# accidental duplicate calls within a single user action, not about serving
# stale metadata for a video whose title/availability may have changed.
_CACHE_TTL_SECONDS = 120


class MetadataExtractor:
    """Validates a URL and extracts its metadata via the appropriate provider.

    Caches successful results per-URL for a short TTL (see _CACHE_TTL_SECONDS) to
    avoid duplicate yt-dlp invocations for the same URL in quick succession.
    """

    def __init__(self, engine: DownloaderEngine) -> None:
        self._engine = engine
        self._cache: dict[str, tuple[float, MediaInfo | PlaylistInfo]] = {}
        self._cache_lock = threading.Lock()

    def extract(self, url: str) -> MediaInfo | PlaylistInfo:
        """Extract metadata for url. Suitable for direct use as FetchWorker's fetch_fn."""
        clean_url = validate_or_raise(url)

        cached = self._get_cached(clean_url)
        if cached is not None:
            _logger.info("Metadata cache hit for %s (skipping yt-dlp call)", clean_url)
            return cached

        provider = self._engine.find_provider(clean_url)
        _logger.info("Metadata cache miss for %s; extracting via provider '%s'", clean_url, provider.name)
        result = provider.extract(clean_url)

        with self._cache_lock:
            self._cache[clean_url] = (time.monotonic(), result)
        return result

    def _get_cached(self, url: str) -> MediaInfo | PlaylistInfo | None:
        with self._cache_lock:
            entry = self._cache.get(url)
            if entry is None:
                return None
            cached_at, result = entry
            if time.monotonic() - cached_at > _CACHE_TTL_SECONDS:
                del self._cache[url]
                return None
            return result

    def invalidate(self, url: str | None = None) -> None:
        """Drop a single cached URL, or the entire cache if url is None."""
        with self._cache_lock:
            if url is None:
                self._cache.clear()
            else:
                self._cache.pop(url, None)
