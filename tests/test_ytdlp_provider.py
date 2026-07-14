# tests/test_ytdlp_provider.py
from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from app.downloader.progress import DownloadCancelledError
from app.downloader.providers import ytdlp_provider as ytdlp_provider_module
from app.downloader.providers.ytdlp_provider import YtDlpError, YtDlpProvider
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo


def _media(title: str = "Video") -> MediaInfo:
    return MediaInfo(id=title, title=title, provider="yt-dlp", source_url="https://example.com/watch")


def _item() -> DownloadItem:
    return DownloadItem(media_info=_media(), destination_path=Path("/tmp/video.mp4"), quality="720p")


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_can_handle_http_and_https_urls():
    provider = YtDlpProvider()

    assert provider.can_handle("https://youtube.com/watch?v=abc") is True
    assert provider.can_handle("ftp://example.com/file") is False


def test_extract_parses_single_video_json(monkeypatch):
    provider = YtDlpProvider()
    payload = {
        "id": "abc123",
        "title": "My Video",
        "webpage_url": "https://youtube.com/watch?v=abc123",
        "thumbnail": "https://example.com/thumb.jpg",
        "duration": 125,
        "uploader": "Someone",
        "formats": [{"vcodec": "avc1", "height": 720}, {"vcodec": "avc1", "height": 1080}],
    }
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout=json.dumps(payload))
    )

    result = provider.extract("https://youtube.com/watch?v=abc123")

    assert result.title == "My Video"
    assert result.available_qualities == ["1080p", "720p"]
    assert result.duration_seconds == 125


def test_extract_parses_playlist_json(monkeypatch):
    provider = YtDlpProvider()
    payload = {
        "_type": "playlist",
        "id": "PL123",
        "title": "My Playlist",
        "thumbnail": None,
        "entries": [
            {"id": "1", "title": "Entry One", "webpage_url": "https://youtube.com/watch?v=1"},
            {"id": "2", "title": "Entry Two", "webpage_url": "https://youtube.com/watch?v=2"},
        ],
    }
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout=json.dumps(payload))
    )

    result = provider.extract("https://youtube.com/playlist?list=PL123")

    assert result.title == "My Playlist"
    assert result.entry_count == 2
    assert [entry.title for entry in result.entries] == ["Entry One", "Entry Two"]


def test_extract_raises_on_nonzero_exit(monkeypatch):
    provider = YtDlpProvider()
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompletedProcess(1, stderr="ERROR: video unavailable")
    )

    with pytest.raises(YtDlpError, match="video unavailable"):
        provider.extract("https://youtube.com/watch?v=missing")


def test_extract_raises_on_invalid_json(monkeypatch):
    provider = YtDlpProvider()
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout="not json"))

    with pytest.raises(YtDlpError):
        provider.extract("https://youtube.com/watch?v=abc")


def test_cookie_candidates_default_to_full_auto_chain():
    provider = YtDlpProvider(cookies_from_browser="auto")

    assert provider._cookie_candidates() == [
        ("chrome", ["--cookies-from-browser", "chrome"]),
        ("edge", ["--cookies-from-browser", "edge"]),
        ("firefox", ["--cookies-from-browser", "firefox"]),
        ("none", []),
    ]


def test_cookie_candidates_auto_chain_appends_cookies_file_before_none():
    provider = YtDlpProvider(cookies_from_browser="auto", cookies_file="/tmp/cookies.txt")

    labels = [label for label, _args in provider._cookie_candidates()]
    assert labels == ["chrome", "edge", "firefox", "cookies.txt", "none"]


def test_extract_falls_back_through_cookie_chain_on_access_error(monkeypatch):
    provider = YtDlpProvider(js_runtime=None, remote_components=None)
    payload = {"id": "abc", "title": "Test Video", "webpage_url": "https://youtube.com/watch?v=abc"}
    attempted_browsers: list[str] = []

    def fake_run(command, **kwargs):
        if "--cookies-from-browser" in command:
            browser = command[command.index("--cookies-from-browser") + 1]
            attempted_browsers.append(browser)
            if browser in ("chrome", "edge"):
                return _FakeCompletedProcess(
                    1, stderr="ERROR: Could not copy Chrome cookie database. See https://github.com/yt-dlp/yt-dlp/issues/7271"
                )
            return _FakeCompletedProcess(0, stdout=json.dumps(payload))
        return _FakeCompletedProcess(1, stderr="unexpected")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = provider.extract("https://youtube.com/watch?v=abc")

    assert result.title == "Test Video"
    assert attempted_browsers == ["chrome", "edge", "firefox"]


def test_extract_does_not_cycle_cookie_chain_for_unrelated_failure(monkeypatch):
    provider = YtDlpProvider(js_runtime=None, remote_components=None)
    call_count = {"n": 0}

    def fake_run(command, **kwargs):
        call_count["n"] += 1
        return _FakeCompletedProcess(1, stderr="ERROR: Video unavailable")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(YtDlpError, match="Video unavailable"):
        provider.extract("https://youtube.com/watch?v=missing")

    # A genuinely invalid video should fail on the very first attempt, not cycle
    # through chrome/edge/firefox/none looking for a cookie source that won't help.
    assert call_count["n"] == 1


def test_extract_raises_actionable_error_when_bot_check_survives_entire_chain(monkeypatch):
    provider = YtDlpProvider(js_runtime=None, remote_components=None)

    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: _FakeCompletedProcess(1, stderr="ERROR: Sign in to confirm you're not a bot"),
    )

    with pytest.raises(YtDlpError, match="no working source was available"):
        provider.extract("https://youtube.com/watch?v=abc")


def test_base_command_includes_ffmpeg_location_when_bundled(monkeypatch, tmp_path):
    provider = YtDlpProvider()
    monkeypatch.setattr(ytdlp_provider_module, "get_ffmpeg_location", lambda: tmp_path)

    command = provider._base_command()

    assert "--ffmpeg-location" in command
    assert str(tmp_path) in command


def test_base_command_omits_ffmpeg_location_when_not_bundled(monkeypatch):
    provider = YtDlpProvider()
    monkeypatch.setattr(ytdlp_provider_module, "get_ffmpeg_location", lambda: None)

    assert "--ffmpeg-location" not in provider._base_command()


def test_auth_and_runtime_args_are_opt_in():
    provider = YtDlpProvider(
        js_runtime=None,
        remote_components="ejs:github",
        cookies_from_browser="chrome",
        impersonate="chrome",
    )

    assert provider._cookie_candidates() == [
        ("chrome", ["--cookies-from-browser", "chrome"]),
        ("none", []),
    ]
    assert provider._non_cookie_auth_args() == ["--impersonate", "chrome"]
    assert provider._runtime_args() == ["--remote-components", "ejs:github"]


def test_js_runtime_auto_detects_node_on_path(monkeypatch):
    monkeypatch.setattr(ytdlp_provider_module.shutil, "which", lambda name: "/usr/bin/node" if name == "node" else None)

    provider = YtDlpProvider()

    assert provider._runtime_args() == ["--js-runtimes", "node", "--remote-components", "ejs:github"]


def test_js_runtime_auto_detect_omitted_when_nothing_on_path(monkeypatch):
    monkeypatch.setattr(ytdlp_provider_module.shutil, "which", lambda name: None)

    provider = YtDlpProvider()

    assert provider._runtime_args() == ["--remote-components", "ejs:github"]


def test_js_runtime_explicit_none_disables_even_if_node_available(monkeypatch):
    monkeypatch.setattr(ytdlp_provider_module.shutil, "which", lambda name: "/usr/bin/node")

    provider = YtDlpProvider(js_runtime=None)

    assert provider._runtime_args() == ["--remote-components", "ejs:github"]


def test_format_selector_includes_wildcard_to_avoid_excluding_dash_formats():
    item = _item()
    item.quality = "480p"

    assert YtDlpProvider._build_format_selector(item) == "bestvideo*[height<=480]+bestaudio/best[height<=480]"


def test_postprocessing_args_audio_only():
    provider = YtDlpProvider()
    item = _item()
    item.audio_only = True
    item.audio_format = "flac"

    assert provider._postprocessing_args(item) == ["--extract-audio", "--audio-format", "flac"]


def test_postprocessing_args_video_merges_to_mkv_with_stream_copy():
    provider = YtDlpProvider()

    assert provider._postprocessing_args(_item()) == [
        "--merge-output-format",
        "mkv",
        "--postprocessor-args",
        "Merger+ffmpeg_o1:-c:v copy -c:a copy",
    ]


def test_postprocessing_args_includes_subtitles_and_chapters_when_enabled():
    provider = YtDlpProvider(write_subtitles=True, subtitle_languages="en,fr", embed_chapters=True)

    args = provider._postprocessing_args(_item())

    assert "--write-subs" in args
    assert "en,fr" in args
    assert "--embed-chapters" in args


class _FakeProcess:
    """Stands in for subprocess.Popen, yielding pre-scripted stdout lines."""

    def __init__(self, lines: list[str], returncode: int = 0) -> None:
        self.stdout = iter(lines)
        self.stderr = _FakeStream("")
        self._returncode = returncode
        self.killed = False

    def wait(self) -> int:
        return self._returncode

    def kill(self) -> None:
        self.killed = True


class _FakeStream:
    def __init__(self, content: str) -> None:
        self._content = content

    def read(self) -> str:
        return self._content


def test_download_streams_progress_and_succeeds(monkeypatch):
    provider = YtDlpProvider()
    lines = [
        json.dumps({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100, "speed": 10.0}),
        "",
    ]
    fake_process = _FakeProcess(lines, returncode=0)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: fake_process)

    received = []
    provider.download(_item(), lambda *args: received.append(args), threading.Event())

    assert received == [(50, 100, 10.0)]


def test_download_raises_ytdlp_error_on_nonzero_exit(monkeypatch):
    provider = YtDlpProvider()
    fake_process = _FakeProcess([], returncode=1)
    fake_process.stderr = _FakeStream("ERROR: network failure")
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: fake_process)

    with pytest.raises(YtDlpError, match="network failure"):
        provider.download(_item(), lambda *args: None, threading.Event())


def test_download_kills_process_and_raises_on_cancellation(monkeypatch):
    provider = YtDlpProvider()
    lines = [
        json.dumps({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 100, "speed": 1.0}),
    ]
    fake_process = _FakeProcess(lines, returncode=0)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: fake_process)

    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(DownloadCancelledError):
        provider.download(_item(), lambda *args: None, cancel_event)

    assert fake_process.killed is True