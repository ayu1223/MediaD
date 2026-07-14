from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.logger import get_logger

_logger = get_logger(__name__)


class MergeError(Exception):
    """Raised when merging separate audio/video streams fails."""


def is_ffmpeg_available() -> bool:
    """Return True if the ffmpeg binary is available on PATH."""
    return shutil.which("ffmpeg") is not None


def merge_streams(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Mux separate video and audio files into a single output file using ffmpeg.

    Raises MergeError if ffmpeg is unavailable or the merge fails.
    """
    if not is_ffmpeg_available():
        raise MergeError("ffmpeg is not installed or not on PATH; cannot merge streams.")
    if not video_path.exists() or not audio_path.exists():
        raise MergeError("Both video and audio source files must exist before merging.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c", "copy",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("ffmpeg merge failed: %s", result.stderr)
        raise MergeError(f"ffmpeg merge failed: {result.stderr.strip()[-500:]}")

    video_path.unlink(missing_ok=True)
    audio_path.unlink(missing_ok=True)
    return output_path
