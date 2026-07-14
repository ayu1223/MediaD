from __future__ import annotations

import re
import shutil
from pathlib import Path

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_FILENAME_LENGTH = 200


def sanitize_filename(name: str) -> str:
    """Strip characters that are invalid in filenames on common filesystems, and trim length."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name).strip().rstrip(".")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:_MAX_FILENAME_LENGTH]


def unique_path(path: Path) -> Path:
    """Return a path guaranteed not to collide with an existing file, appending ' (n)' if needed."""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def ensure_directory(path: Path) -> Path:
    """Create the directory (and parents) if it doesn't exist, and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def free_space_bytes(path: Path) -> int:
    """Return the number of free bytes available on the filesystem containing path."""
    target = path if path.exists() else path.parent
    return shutil.disk_usage(target).free


def delete_file(path: Path) -> bool:
    """Delete a file if it exists. Returns True if a file was removed."""
    if path.is_file():
        path.unlink()
        return True
    return False
