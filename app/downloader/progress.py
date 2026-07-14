from __future__ import annotations

import threading
import time
from collections.abc import Callable

ProgressCallback = Callable[[int, int, float], None]

_MIN_EMIT_INTERVAL_SECONDS = 0.2


class DownloadCancelledError(Exception):
    """Raised inside a provider's download loop when cancellation is requested mid-transfer."""


def build_progress_hook(
    progress_cb: ProgressCallback, cancel_event: threading.Event
) -> Callable[[dict], None]:
    """Return a yt-dlp-style progress hook that forwards throttled updates to progress_cb.

    Raises DownloadCancelledError if cancel_event is set, which the caller's download
    loop should let propagate so the worker records the item as cancelled.
    """
    last_emit_time = 0.0

    def hook(status: dict) -> None:
        nonlocal last_emit_time
        if cancel_event.is_set():
            raise DownloadCancelledError("Download cancelled by user.")

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
