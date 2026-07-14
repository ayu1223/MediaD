from __future__ import annotations

import pytest

from app.downloader.engine import DownloaderEngine
from app.downloader.metadata import MetadataExtractor
from app.downloader.providers.base import Provider
from app.downloader.validators import InvalidURLError
from app.models.media_info import MediaInfo


class _StubProvider(Provider):
    name = "stub"

    def __init__(self) -> None:
        self.extract_calls: list[str] = []

    def can_handle(self, url: str) -> bool:
        return True

    def extract(self, url: str) -> MediaInfo:
        self.extract_calls.append(url)
        return MediaInfo(id="1", title="Video", provider=self.name, source_url=url)

    def download(self, item, progress_cb, cancel_event) -> None:
        raise NotImplementedError


def test_extract_delegates_to_resolved_provider():
    provider = _StubProvider()
    engine = DownloaderEngine(providers=[provider])
    extractor = MetadataExtractor(engine)

    result = extractor.extract("https://example.com/video")

    assert result.title == "Video"
    assert provider.extract_calls == ["https://example.com/video"]


def test_extract_trims_url_before_dispatch():
    provider = _StubProvider()
    engine = DownloaderEngine(providers=[provider])
    extractor = MetadataExtractor(engine)

    extractor.extract("  https://example.com/video  ")

    assert provider.extract_calls == ["https://example.com/video"]


def test_extract_raises_on_invalid_url():
    engine = DownloaderEngine(providers=[_StubProvider()])
    extractor = MetadataExtractor(engine)

    with pytest.raises(InvalidURLError):
        extractor.extract("not a url")
