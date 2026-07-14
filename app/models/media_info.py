from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MediaInfo:
    """Provider-agnostic metadata for a single piece of media, as returned by extraction."""

    id: str
    title: str
    provider: str
    source_url: str
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    uploader: str | None = None
    available_qualities: list[str] = field(default_factory=list)
    available_audio_formats: list[str] = field(default_factory=list)
    is_playlist_entry: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def display_duration(self) -> str:
        """Return the duration formatted as H:MM:SS or M:SS, or an empty string if unknown."""
        if self.duration_seconds is None:
            return ""
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
