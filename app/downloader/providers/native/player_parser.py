from __future__ import annotations

from app.core.logger import get_logger

from .constants import CLIENT_CONTEXTS, PLAYER_CLIENT_ORDER
from .exceptions import NativeExtractionError
from .utils import call_player_api

_logger = get_logger(__name__)

_PLAYABLE_STATUSES = {"OK"}


def fetch_playable_response(video_id: str) -> dict:
    """Return a playable InnerTube player response for video_id, trying each
    client context in PLAYER_CLIENT_ORDER until one succeeds.

    Raises NativeExtractionError if every client context fails or reports the
    video as unplayable (private, age-restricted without auth, region-blocked,
    live-only, etc.) — callers should treat this as "let yt-dlp handle it",
    since yt-dlp has broader client support and cookie-based auth for the cases
    a bare anonymous InnerTube call can't reach.
    """
    last_status: str | None = None

    for client_name in PLAYER_CLIENT_ORDER:
        client_context = CLIENT_CONTEXTS[client_name]
        response = call_player_api(video_id, client_context)
        if response is None:
            continue

        playability = response.get("playabilityStatus", {})
        status = playability.get("status")
        if status in _PLAYABLE_STATUSES and response.get("streamingData"):
            _logger.info("Native player response OK for %s using client '%s'", video_id, client_name)
            return response

        last_status = status
        _logger.info(
            "Native player response for %s via '%s' not playable (status=%s); trying next client.",
            video_id, client_name, status,
        )

    raise NativeExtractionError(
        f"No InnerTube client context returned a playable response for {video_id} "
        f"(last status: {last_status})."
    )


def parse_basic_metadata(player_response: dict) -> dict:
    """Extract the plain metadata fields (title, uploader, duration, thumbnail)
    from a player response's videoDetails, tolerating missing fields."""
    details = player_response.get("videoDetails", {}) or {}
    thumbnails = (details.get("thumbnail", {}) or {}).get("thumbnails", []) or []
    best_thumbnail = thumbnails[-1]["url"] if thumbnails else None

    duration_raw = details.get("lengthSeconds")
    try:
        duration_seconds = int(duration_raw) if duration_raw is not None else None
    except (TypeError, ValueError):
        duration_seconds = None

    return {
        "id": details.get("videoId"),
        "title": details.get("title") or "Untitled",
        "uploader": details.get("author"),
        "duration_seconds": duration_seconds,
        "thumbnail_url": best_thumbnail,
    }