from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from app.core.constants import CONFIG_FILE_NAME, DATABASE_FILE_NAME, THUMBNAIL_CACHE_DIRNAME
from app.core.version import ORG_NAME

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent


def get_project_root() -> Path:
    """Return the root directory of the installed/checked-out application."""
    return _PROJECT_ROOT


def get_app_data_dir() -> Path:
    """Return the platform-appropriate directory for persistent application data."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        path = Path(base) / ORG_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / ORG_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        path = Path(base) / ORG_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_dir() -> Path:
    """Return the platform-appropriate directory for user configuration."""
    if sys.platform == "win32":
        return get_app_data_dir()
    if sys.platform == "darwin":
        return get_app_data_dir()
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    path = Path(base) / ORG_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_dir() -> Path:
    """Return the directory where rotating log files are written."""
    path = get_app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file_path() -> Path:
    """Return the full path to the user's writable configuration file."""
    return get_config_dir() / CONFIG_FILE_NAME


def get_config_template_path() -> Path:
    """Return the path to the read-only default configuration template shipped with the app."""
    return _PACKAGE_ROOT / "config" / CONFIG_FILE_NAME


def get_database_path() -> Path:
    """Return the full path to the SQLite database file."""
    return get_app_data_dir() / DATABASE_FILE_NAME


def get_default_download_dir() -> Path:
    """Return the OS default Downloads folder, falling back to the project's downloads/ directory."""
    home_downloads = Path.home() / "Downloads"
    if home_downloads.is_dir():
        return home_downloads
    fallback = _PROJECT_ROOT / "downloads"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_thumbnail_cache_dir() -> Path:
    """Return the directory used to cache downloaded thumbnail images."""
    path = get_app_data_dir() / THUMBNAIL_CACHE_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_ffmpeg_location() -> Path | None:
    """Return a directory containing ffmpeg/ffprobe, preferring a bundled copy.

    Checks resources/ffmpeg/ first (populated by placing platform binaries there before
    packaging — see resources/ffmpeg/README.md), then falls back to whatever "ffmpeg"
    resolves to on PATH. Returns None only if neither is found, in which case callers
    should omit --ffmpeg-location and let yt-dlp/ffmpeg-dependent code report its own
    "ffmpeg not found" error rather than silently downloading without it.
    """
    ffmpeg_dir = get_project_root() / "resources" / "ffmpeg"
    binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    if (ffmpeg_dir / binary_name).is_file():
        return ffmpeg_dir

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg).resolve().parent
    return None
