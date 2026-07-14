from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(slots=True)
class HistoryItem:
    """A completed download, as persisted in the history repository."""

    id: str
    title: str
    provider: str
    source_url: str
    file_path: Path
    media_type: MediaType
    quality: str
    file_size_bytes: int
    completed_at: datetime
    thumbnail_url: str | None = None
