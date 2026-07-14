from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.logger import get_logger

_logger = get_logger(__name__)


def embed_thumbnail(media_path: Path, thumbnail_path: Path) -> bool:
    """Embed thumbnail_path as cover art into media_path in place. Returns True on success.

    No-ops (returns False) if ffmpeg is unavailable rather than raising, since a missing
    thumbnail embed should never fail an otherwise-successful download.
    """
    if shutil.which("ffmpeg") is None:
        _logger.warning("ffmpeg not available; skipping thumbnail embed for %s", media_path)
        return False
    if not media_path.exists() or not thumbnail_path.exists():
        _logger.warning("Missing source file(s) for thumbnail embed: %s / %s", media_path, thumbnail_path)
        return False

    temp_output = media_path.with_suffix(f".embed{media_path.suffix}")
    command = [
        "ffmpeg",
        "-y",
        "-i", str(media_path),
        "-i", str(thumbnail_path),
        "-map", "0",
        "-map", "1",
        "-c", "copy",
        "-disposition:v:1", "attached_pic",
        str(temp_output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("ffmpeg thumbnail embed failed: %s", result.stderr)
        temp_output.unlink(missing_ok=True)
        return False

    temp_output.replace(media_path)
    return True
