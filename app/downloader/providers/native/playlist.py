from __future__ import annotations

from app.core.logger import get_logger
from app.utils.network import http_post_json

from .constants import INNERTUBE_API_KEY, INNERTUBE_BROWSE_URL, REQUEST_TIMEOUT_SECONDS, WEB_CLIENT_CONTEXT
from .exceptions import NativeExtractionError

_logger = get_logger(__name__)


def fetch_playlist(playlist_id: str) -> tuple[str, list[dict]]:
    """Return (playlist_title, entries) for playlist_id, where each entry is a
    dict with keys: video_id, title, uploader, duration_seconds, thumbnail_url.

    Raises NativeExtractionError if the browse call fails or the (famously deep
    and version-sensitive) response structure can't be walked — the composite
    provider treats that as "let yt-dlp handle this playlist instead", which has
    its own, actively-maintained playlist extraction.
    """
    payload = {
        "context": {"client": WEB_CLIENT_CONTEXT},
        "browseId": f"VL{playlist_id}",
    }
    url = f"{INNERTUBE_BROWSE_URL}?key={INNERTUBE_API_KEY}"
    response = http_post_json(url, payload, timeout=REQUEST_TIMEOUT_SECONDS)
    if response is None:
        raise NativeExtractionError(f"InnerTube browse call failed for playlist {playlist_id}.")

    title = _extract_playlist_title(response)
    entries = _extract_playlist_entries(response)
    if not entries:
        raise NativeExtractionError(f"Could not parse any entries for playlist {playlist_id}.")

    return title, entries


def _extract_playlist_title(response: dict) -> str:
    try:
        header = response.get("header", {})
        renderer = header.get("playlistHeaderRenderer") or {}
        title = renderer.get("title", {})
        if "simpleText" in title:
            return title["simpleText"]
        runs = title.get("runs") or []
        if runs:
            return runs[0].get("text", "Untitled Playlist")
    except (AttributeError, TypeError):
        pass
    return "Untitled Playlist"


def _extract_playlist_entries(response: dict) -> list[dict]:
    try:
        tabs = response["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
        section_list = tabs[0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]
        item_section = section_list[0]["itemSectionRenderer"]["contents"]
        raw_entries = item_section[0]["playlistVideoListRenderer"]["contents"]
    except (KeyError, IndexError, TypeError) as error:
        _logger.warning("Could not walk InnerTube playlist response structure: %s", error)
        return []

    entries: list[dict] = []
    for raw in raw_entries:
        renderer = raw.get("playlistVideoRenderer")
        if not renderer:
            continue  # e.g. a "continuation" item renderer — not an actual video entry

        video_id = renderer.get("videoId")
        if not video_id:
            continue

        title = _first_text(renderer.get("title"))
        uploader = _first_text(renderer.get("shortBylineText"))
        thumbnails = (renderer.get("thumbnail", {}) or {}).get("thumbnails", []) or []

        length_raw = renderer.get("lengthSeconds")
        try:
            duration_seconds = int(length_raw) if length_raw is not None else None
        except (TypeError, ValueError):
            duration_seconds = None

        entries.append(
            {
                "video_id": video_id,
                "title": title or "Untitled",
                "uploader": uploader,
                "duration_seconds": duration_seconds,
                "thumbnail_url": thumbnails[-1]["url"] if thumbnails else None,
            }
        )
    return entries


def _first_text(text_field: dict | None) -> str | None:
    if not text_field:
        return None
    if "simpleText" in text_field:
        return text_field["simpleText"]
    runs = text_field.get("runs") or []
    return runs[0].get("text") if runs else None