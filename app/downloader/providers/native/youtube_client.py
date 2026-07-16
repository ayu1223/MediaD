from __future__ import annotations

from app.core.constants import SUPPORTED_AUDIO_FORMATS
from app.core.logger import get_logger
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

from . import playlist as playlist_module
from .exceptions import CipherRequiredError, NativeExtractionError
from .formats import StreamFormat, available_video_qualities, parse_formats
from .player_parser import fetch_playable_response, parse_basic_metadata

_logger = get_logger(__name__)

PROVIDER_NAME = "youtube-native"


def extract_video(video_id: str, source_url: str) -> MediaInfo:
    """Fetch and parse a single video's metadata into a MediaInfo."""
    player_response = fetch_playable_response(video_id)
    basic = parse_basic_metadata(player_response)
    formats = parse_formats(player_response)

    if not formats:
        raise CipherRequiredError(
            f"No usable (non-cipher-gated) formats available for {video_id}; "
            "falling back to yt-dlp, which implements full cipher support."
        )

    qualities = available_video_qualities(formats)
    return MediaInfo(
        id=basic["id"] or video_id,
        title=basic["title"],
        provider=PROVIDER_NAME,
        source_url=source_url,
        thumbnail_url=basic["thumbnail_url"],
        duration_seconds=basic["duration_seconds"],
        uploader=basic["uploader"],
        available_qualities=qualities,
        available_audio_formats=list(SUPPORTED_AUDIO_FORMATS),
    )


def extract_playlist(playlist_id: str, source_url: str) -> PlaylistInfo:
    """Fetch and parse a playlist's metadata + entries into a PlaylistInfo.

    Entries are built from the lightweight browse-endpoint listing (title,
    uploader, duration, thumbnail) without a per-entry player call — resolving
    exact per-entry stream formats happens lazily, only for entries the user
    actually chooses to download (see get_download_formats), to avoid N extra
    network calls for a playlist the user is just browsing.
    """
    title, raw_entries = playlist_module.fetch_playlist(playlist_id)

    entries = [
        MediaInfo(
            id=entry["video_id"],
            title=entry["title"],
            provider=PROVIDER_NAME,
            source_url=f"https://www.youtube.com/watch?v={entry['video_id']}",
            thumbnail_url=entry["thumbnail_url"],
            duration_seconds=entry["duration_seconds"],
            uploader=entry["uploader"],
            available_audio_formats=list(SUPPORTED_AUDIO_FORMATS),
        )
        for entry in raw_entries
    ]

    return PlaylistInfo(
        id=playlist_id,
        title=title,
        provider=PROVIDER_NAME,
        source_url=source_url,
        thumbnail_url=entries[0].thumbnail_url if entries else None,
        entries=entries,
    )


def get_download_formats(video_id: str) -> list[StreamFormat]:
    """Fetch a fresh set of stream formats for video_id, suitable for immediate
    download. Called at download time (not extract time) so stream URLs — which
    InnerTube issues with a limited validity window — are as fresh as possible,
    including for playlist entries that were only lightly parsed at extract time.
    """
    player_response = fetch_playable_response(video_id)
    formats = parse_formats(player_response)
    if not formats:
        raise CipherRequiredError(f"No usable formats available for {video_id} at download time.")
    return formats