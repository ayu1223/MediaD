from __future__ import annotations

from pathlib import Path

from app.models.download_item import DownloadItem, DownloadStatus
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo
from app.models.settings import AppSettings


def _media() -> MediaInfo:
    return MediaInfo(id="1", title="Video", provider="test", source_url="https://example.com")


def test_download_item_is_active_true_for_downloading_and_merging():
    item = DownloadItem(media_info=_media(), destination_path=Path("/tmp/x.mp4"), quality="720p")

    item.status = DownloadStatus.DOWNLOADING
    assert item.is_active() is True
    item.status = DownloadStatus.MERGING
    assert item.is_active() is True
    item.status = DownloadStatus.QUEUED
    assert item.is_active() is False


def test_download_item_is_finished_true_for_terminal_states():
    item = DownloadItem(media_info=_media(), destination_path=Path("/tmp/x.mp4"), quality="720p")

    for status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
        item.status = status
        assert item.is_finished() is True

    item.status = DownloadStatus.DOWNLOADING
    assert item.is_finished() is False


def test_download_item_generates_unique_ids():
    a = DownloadItem(media_info=_media(), destination_path=Path("/tmp/a.mp4"), quality="720p")
    b = DownloadItem(media_info=_media(), destination_path=Path("/tmp/b.mp4"), quality="720p")

    assert a.id != b.id


def test_media_info_display_duration_formats_hours_minutes_seconds():
    assert MediaInfo(id="1", title="t", provider="p", source_url="u", duration_seconds=3725).display_duration() == "1:02:05"


def test_media_info_display_duration_formats_minutes_seconds():
    assert MediaInfo(id="1", title="t", provider="p", source_url="u", duration_seconds=65).display_duration() == "1:05"


def test_media_info_display_duration_empty_when_unknown():
    assert MediaInfo(id="1", title="t", provider="p", source_url="u").display_duration() == ""


def test_playlist_info_entry_count():
    playlist = PlaylistInfo(id="p", title="Playlist", provider="p", source_url="u", entries=[_media(), _media()])

    assert playlist.entry_count == 2


def test_app_settings_from_dict_ignores_unknown_keys():
    settings = AppSettings.from_dict({"theme": "light", "unknown_field": "value"})

    assert settings.theme == "light"
    assert not hasattr(settings, "unknown_field")


def test_app_settings_round_trips_through_dict():
    original = AppSettings(theme="light", max_concurrent_downloads=7)

    restored = AppSettings.from_dict(original.to_dict())

    assert restored == original
