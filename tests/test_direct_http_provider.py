from __future__ import annotations

from app.downloader.providers.direct_http_provider import DirectHttpProvider


def test_can_handle_recognizes_direct_media_extensions():
    provider = DirectHttpProvider()

    assert provider.can_handle("https://example.com/video.mp4") is True
    assert provider.can_handle("https://example.com/song.mp3") is True


def test_can_handle_rejects_non_media_paths():
    provider = DirectHttpProvider()

    assert provider.can_handle("https://example.com/watch?v=abc") is False
    assert provider.can_handle("https://example.com/page.html") is False


def test_extract_builds_media_info_from_filename():
    provider = DirectHttpProvider()

    info = provider.extract("https://example.com/videos/My Clip.mp4")

    assert info.title == "My Clip.mp4"
    assert info.id == "My Clip.mp4"
    assert info.provider == "direct"
    assert info.available_qualities == ["original"]
    assert info.extra["extension"] == "mp4"


def test_extract_falls_back_to_download_for_extensionless_url():
    provider = DirectHttpProvider()

    info = provider.extract("https://example.com/")

    assert info.title == "download"
    assert info.extra["extension"] == "bin"
