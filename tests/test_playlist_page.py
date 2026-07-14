from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo
from app.ui.pages.playlist_page import PlaylistPage


@pytest.fixture
def page():
    entries = [
        MediaInfo(id=str(i), title=f"Video {i}", provider="yt-dlp", source_url="https://example.com")
        for i in range(5)
    ]
    playlist = PlaylistInfo(id="p", title="Playlist", provider="yt-dlp", source_url="https://example.com", entries=entries)
    widget = PlaylistPage(MagicMock(), "/tmp/downloads")
    widget.load_playlist(playlist)
    return widget


def _checked_states(page: PlaylistPage) -> list[bool]:
    return [row.checkbox.isChecked() for row in page._rows]


def test_entries_are_all_selected_by_default(page):
    assert _checked_states(page) == [True] * 5


def test_deselect_unchecks_every_row(page):
    page._banner.deselect_btn.click()

    assert _checked_states(page) == [False] * 5


def test_select_all_rechecks_every_row(page):
    page._banner.deselect_btn.click()
    page._banner.select_all_btn.click()

    assert _checked_states(page) == [True] * 5


def test_unchecking_one_row_updates_selection_count_label(page):
    page._rows[0].checkbox.setChecked(False)

    assert page._selection_lbl.text() == "4 videos selected"


def test_download_button_disabled_when_nothing_selected(page):
    page._banner.deselect_btn.click()

    assert page.dl_btn.isEnabled() is False


def test_download_enqueues_only_checked_entries(page):
    page._rows[0].checkbox.setChecked(False)
    page._rows[1].checkbox.setChecked(False)

    page._on_download_clicked()

    assert page._download_service.enqueue_playlist.called
    enqueued_playlist = page._download_service.enqueue_playlist.call_args[0][0]
    assert [entry.title for entry in enqueued_playlist.entries] == ["Video 2", "Video 3", "Video 4"]
