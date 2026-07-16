from __future__ import annotations

from app.downloader.providers.base import Provider
from app.downloader.providers.direct_http_provider import DirectHttpProvider
from app.downloader.providers.youtube_provider import YouTubeProvider
from app.downloader.providers.ytdlp_provider import YtDlpProvider


class UnsupportedURLError(Exception):
    """Raised when no registered provider can handle a given URL."""


class DownloaderEngine:
    """Owns the ordered list of registered providers and resolves URLs to the right one."""

    def __init__(self, providers: list[Provider] | None = None, cookies_file: str | None = None) -> None:
        self._providers: list[Provider] = providers if providers is not None else self._default_providers(cookies_file)

    @staticmethod
    def _default_providers(cookies_file: str | None = None) -> list[Provider]:
        # Issue 7/8: YouTube URLs go through the composite YouTubeProvider (tries
        # the native InnerTube-based extractor first, transparently falls back to
        # yt-dlp — see providers/youtube_provider.py) ahead of the generic
        # YtDlpProvider, which remains registered afterward as the catch-all for
        # every other supported site (Vimeo, Twitter/X, etc).
        return [
            DirectHttpProvider(),
            YouTubeProvider(YtDlpProvider(cookies_file=cookies_file)),
            YtDlpProvider(cookies_file=cookies_file),
        ]

    def set_cookies_file(self, cookies_file: str | None) -> None:
        """Propagate an updated cookies.txt path to every provider that supports it."""
        for provider in self._providers:
            setter = getattr(provider, "set_cookies_file", None)
            if callable(setter):
                setter(cookies_file)

    def register(self, provider: Provider, priority: bool = False) -> None:
        """Register a new provider. If priority is True, it is checked before existing providers."""
        if priority:
            self._providers.insert(0, provider)
        else:
            self._providers.append(provider)

    def find_provider(self, url: str) -> Provider:
        """Return the first registered provider that can handle url, or raise UnsupportedURLError."""
        for provider in self._providers:
            if provider.can_handle(url):
                return provider
        raise UnsupportedURLError(f"No registered provider can handle: {url}")