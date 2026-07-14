from __future__ import annotations

import pytest

from app.downloader.engine import DownloaderEngine, UnsupportedURLError
from app.downloader.providers.base import Provider


class _StubProvider(Provider):
    def __init__(self, name: str, handles: bool) -> None:
        self.name = name
        self._handles = handles

    def can_handle(self, url: str) -> bool:
        return self._handles

    def extract(self, url: str):
        raise NotImplementedError

    def download(self, item, progress_cb, cancel_event) -> None:
        raise NotImplementedError


def test_find_provider_returns_first_matching_provider():
    matching = _StubProvider("match", handles=True)
    engine = DownloaderEngine(providers=[_StubProvider("skip", handles=False), matching])

    assert engine.find_provider("https://example.com") is matching


def test_find_provider_raises_when_none_match():
    engine = DownloaderEngine(providers=[_StubProvider("skip", handles=False)])

    with pytest.raises(UnsupportedURLError):
        engine.find_provider("https://example.com")


def test_register_appends_by_default():
    first = _StubProvider("first", handles=True)
    second = _StubProvider("second", handles=True)
    engine = DownloaderEngine(providers=[first])

    engine.register(second)

    assert engine.find_provider("https://example.com") is first


def test_register_with_priority_is_checked_first():
    first = _StubProvider("first", handles=True)
    priority = _StubProvider("priority", handles=True)
    engine = DownloaderEngine(providers=[first])

    engine.register(priority, priority=True)

    assert engine.find_provider("https://example.com") is priority


def test_default_providers_order_direct_http_before_ytdlp():
    from app.downloader.providers.direct_http_provider import DirectHttpProvider
    from app.downloader.providers.ytdlp_provider import YtDlpProvider

    engine = DownloaderEngine()

    assert isinstance(engine.find_provider("https://example.com/video.mp4"), DirectHttpProvider)
    assert isinstance(engine.find_provider("https://example.com/watch?v=1"), YtDlpProvider)
