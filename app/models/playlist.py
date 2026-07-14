from __future__ import annotations

from dataclasses import dataclass, field

from app.models.media_info import MediaInfo


@dataclass(slots=True)
class PlaylistInfo:
    """Provider-agnostic metadata for a playlist and its constituent media entries."""

    id: str
    title: str
    provider: str
    source_url: str
    thumbnail_url: str | None = None
    entries: list[MediaInfo] = field(default_factory=list)

    @property
    def entry_count(self) -> int:
        return len(self.entries)
