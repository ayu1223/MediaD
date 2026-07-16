from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.logger import get_logger
from app.core.paths import get_ffmpeg_location

_logger = get_logger(__name__)


class MergeError(Exception):
    """Raised when merging separate audio/video streams fails."""


def _resolve_ffmpeg_binary() -> str | None:
    """Return a full path (or bare command name) usable to invoke ffmpeg.

    Prefers a bundled copy (see get_ffmpeg_location), falling back to whatever
    "ffmpeg" resolves to on PATH. This was previously PATH-only (via
    shutil.which), which silently ignored a bundled resources/ffmpeg/ binary —
    the same one YtDlpProvider already passes via --ffmpeg-location — so a
    machine with only the bundled copy and nothing on PATH would incorrectly
    report ffmpeg as unavailable for merging native-extractor downloads.
    """
    ffmpeg_dir = get_ffmpeg_location()
    if ffmpeg_dir is None:
        return None
    binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    candidate = ffmpeg_dir / binary_name
    return str(candidate) if candidate.is_file() else binary_name


def is_ffmpeg_available() -> bool:
    """Return True if an ffmpeg binary (bundled or on PATH) is available."""
    return _resolve_ffmpeg_binary() is not None


def merge_streams(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Mux separate video and audio files into a single output file using ffmpeg.

    Raises MergeError if ffmpeg is unavailable or the merge fails.
    """
    ffmpeg_binary = _resolve_ffmpeg_binary()
    if ffmpeg_binary is None:
        raise MergeError("ffmpeg is not installed or not on PATH; cannot merge streams.")
    if not video_path.exists() or not audio_path.exists():
        raise MergeError("Both video and audio source files must exist before merging.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_binary,
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