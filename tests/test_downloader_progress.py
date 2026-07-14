from __future__ import annotations

import threading
import time

import pytest

from app.downloader.progress import DownloadCancelledError, build_progress_hook


def test_hook_ignores_non_downloading_status():
    calls = []
    hook = build_progress_hook(lambda *args: calls.append(args), threading.Event())

    hook({"status": "finished"})

    assert calls == []


def test_hook_forwards_first_downloading_update():
    calls = []
    hook = build_progress_hook(lambda *args: calls.append(args), threading.Event())

    hook({"status": "downloading", "downloaded_bytes": 100, "total_bytes": 1000, "speed": 50.0})

    assert calls == [(100, 1000, 50.0)]


def test_hook_throttles_rapid_successive_updates():
    calls = []
    hook = build_progress_hook(lambda *args: calls.append(args), threading.Event())

    hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 100, "speed": 1.0})
    hook({"status": "downloading", "downloaded_bytes": 2, "total_bytes": 100, "speed": 1.0})

    assert len(calls) == 1


def test_hook_emits_again_after_interval_elapses():
    calls = []
    hook = build_progress_hook(lambda *args: calls.append(args), threading.Event())

    hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 100, "speed": 1.0})
    time.sleep(0.25)
    hook({"status": "downloading", "downloaded_bytes": 2, "total_bytes": 100, "speed": 1.0})

    assert len(calls) == 2


def test_hook_raises_when_cancelled():
    cancel_event = threading.Event()
    cancel_event.set()
    hook = build_progress_hook(lambda *args: None, cancel_event)

    with pytest.raises(DownloadCancelledError):
        hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 100})


def test_hook_uses_total_bytes_estimate_when_total_missing():
    calls = []
    hook = build_progress_hook(lambda *args: calls.append(args), threading.Event())

    hook({"status": "downloading", "downloaded_bytes": 10, "total_bytes_estimate": 200})

    assert calls == [(10, 200, 0.0)]
