from __future__ import annotations

import threading
import time
from collections.abc import Callable

ProgressCallback = Callable[[int, int, float], None]

_MIN_EMIT_INTERVAL_SECONDS = 0.2


class DownloadCancelledError(Exception):
    """Raised inside a provider's download loop when cancellation is requested mid-transfer."""


class DownloadPausedError(Exception):
    """Raised inside a provider's download loop when a pause is requested mid-transfer.

    Distinct from DownloadCancelledError: a provider catching this must leave any
    partial output (e.g. yt-dlp's .part file, or a partially-written direct-download
    file) in place rather than deleting it, since a pause is expected to be resumed
    later from exactly where it left off (see DownloadWorker.request_pause and
    DownloadManager.resume).
    """


def build_progress_hook(
    progress_cb: ProgressCallback,
    cancel_event: threading.Event,
    pause_event: threading.Event | None = None,
) -> Callable[[dict], None]:
    """Return a yt-dlp-style progress hook that forwards throttled updates to progress_cb.

    Raises DownloadCancelledError if cancel_event is set, or DownloadPausedError if
    pause_event is set (cancellation takes precedence if both are somehow set at
    once), which the caller's download loop should let propagate so the worker
    records the item as cancelled or paused respectively.
    """
    last_emit_time = 0.0

    def hook(status: dict) -> None:
        nonlocal last_emit_time
        if cancel_event.is_set():
            raise DownloadCancelledError("Download cancelled by user.")
        if pause_event is not None and pause_event.is_set():
            raise DownloadPausedError("Download paused by user.")

        if status.get("status") != "downloading":
            return

        now = time.monotonic()
        if now - last_emit_time < _MIN_EMIT_INTERVAL_SECONDS:
            return
        last_emit_time = now

        downloaded = status.get("downloaded_bytes") or 0
        total = status.get("total_bytes") or status.get("total_bytes_estimate") or 0
        speed = status.get("speed") or 0.0
        progress_cb(downloaded, total, speed)

    return hook