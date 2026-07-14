from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.constants import DEFAULT_MAX_CONCURRENT_DOWNLOADS, SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_QUALITIES

_CONFIG_VERSION = 1


@dataclass(slots=True)
class AppSettings:
    """Typed representation of the application's persisted configuration."""

    version: int = _CONFIG_VERSION
    download_directory: str = ""
    max_concurrent_downloads: int = DEFAULT_MAX_CONCURRENT_DOWNLOADS
    default_video_quality: str = SUPPORTED_VIDEO_QUALITIES[2]
    default_audio_format: str = SUPPORTED_AUDIO_FORMATS[0]
    theme: str = "dark"
    window_geometry: dict[str, int] | None = None
    confirm_before_delete: bool = True
    check_for_updates: bool = True
    cookies_file: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        """Build an AppSettings instance from a raw config dict, ignoring unknown keys."""
        known_fields = {f for f in cls.__dataclass_fields__}
        filtered = {key: value for key, value in data.items() if key in known_fields}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this settings instance back into a JSON-compatible dict."""
        return asdict(self)
