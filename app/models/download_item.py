from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from app.models.media_info import MediaInfo


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class DownloadItem:
    """A single entry in the download queue, tracking both request parameters and live progress."""

    media_info: MediaInfo
    destination_path: Path
    quality: str
    audio_only: bool = False
    audio_format: str | None = None

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: DownloadStatus = DownloadStatus.QUEUED
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_bytes_per_sec: float = 0.0
    eta_seconds: int | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.status in (DownloadStatus.DOWNLOADING, DownloadStatus.MERGING)

    def is_finished(self) -> bool:
        return self.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED)
