from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from app.core.logger import get_logger
from app.utils.network import http_post_json

from .constants import INNERTUBE_API_KEY, INNERTUBE_PLAYER_URL, REQUEST_TIMEOUT_SECONDS

_logger = get_logger(__name__)

_YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "music.youtube.com")

_VIDEO_ID_PATH_RE = re.compile(r"^/(?:shorts|embed|live)/([A-Za-z0-9_-]{11})")
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def is_youtube_url(url: str) -> bool:
    """Return True if url's host is a recognized YouTube domain."""
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return False
    return any(host == candidate or host.endswith(f".{candidate}") for candidate in _YOUTUBE_HOSTS)


def extract_video_id(url: str) -> str | None:
    """Return the 11-character video ID from a YouTube URL, or None if not a video URL.

    Handles youtube.com/watch?v=ID, youtu.be/ID, /shorts/ID, /embed/ID, /live/ID.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if not is_youtube_url(url):
        return None

    if host in ("youtu.be",) or host.endswith(".youtu.be"):
        candidate = parsed.path.strip("/").split("/")[0]
        return candidate if _VIDEO_ID_RE.match(candidate) else None

    path_match = _VIDEO_ID_PATH_RE.match(parsed.path)
    if path_match:
        return path_match.group(1)

    query = parse_qs(parsed.query)
    video_ids = query.get("v")
    if video_ids and _VIDEO_ID_RE.match(video_ids[0]):
        return video_ids[0]
    return None


def extract_playlist_id(url: str) -> str | None:
    """Return the playlist ID from a YouTube URL's `list` query parameter, if present."""
    query = parse_qs(urlparse(url).query)
    playlist_ids = query.get("list")
    return playlist_ids[0] if playlist_ids else None


def call_player_api(video_id: str, client_context: dict) -> dict | None:
    """Call InnerTube's /player endpoint for video_id using the given client context.

    Returns the raw parsed JSON response, or None on any network/parse failure.
    """
    payload = {
        "context": {"client": client_context},
        "videoId": video_id,
        "contentCheckOk": True,
        "racyCheckOk": True,
    }
    url = f"{INNERTUBE_PLAYER_URL}?key={INNERTUBE_API_KEY}"
    response = http_post_json(url, payload, timeout=REQUEST_TIMEOUT_SECONDS)
    if response is None:
        _logger.warning("InnerTube player call failed for video %s (client=%s)", video_id, client_context.get("clientName"))
    return response