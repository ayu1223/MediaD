from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.logger import get_logger
from app.core.paths import get_thumbnail_cache_dir
from app.utils.network import http_get

_logger = get_logger(__name__)

_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


class ThumbnailService:
    """Fetches and caches thumbnail images referenced by MediaInfo.thumbnail_url."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or get_thumbnail_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_path(self, url: str) -> Path | None:
        """Return the local cached path for a thumbnail URL if it has already been fetched."""
        cache_key = self._cache_key(url)
        matches = list(self._cache_dir.glob(f"{cache_key}.*"))
        return matches[0] if matches else None

    def fetch(self, url: str) -> Path | None:
        """Fetch a thumbnail, caching it locally. Returns the cached path, or None on failure.

        This performs a blocking network call and must be invoked from a background
        thread (see workers/thumbnail_worker.py), never from the UI thread.
        """
        cached = self.get_cached_path(url)
        if cached is not None:
            return cached

        response = http_get(url)
        if response is None or response.status_code != 200:
            _logger.warning("Failed to fetch thumbnail from %s", url)
            return None

        extension = _EXTENSION_BY_CONTENT_TYPE.get(response.content_type or "", "jpg")
        destination = self._cache_dir / f"{self._cache_key(url)}.{extension}"
        destination.write_bytes(response.content)
        return destination

    @staticmethod
    def _cache_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()
