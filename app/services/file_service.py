from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.logger import get_logger
from app.utils.file_utils import delete_file, ensure_directory, free_space_bytes, sanitize_filename, unique_path

_logger = get_logger(__name__)


class FileService:
    """UI-facing filesystem operations, kept independent of download or provider logic."""

    def build_destination_path(self, directory: Path, filename: str, extension: str) -> Path:
        """Build a collision-free, filesystem-safe destination path for a new download."""
        ensure_directory(directory)
        safe_name = sanitize_filename(filename)
        candidate = directory / f"{safe_name}.{extension.lstrip('.')}"
        return unique_path(candidate)

    def has_sufficient_space(self, directory: Path, required_bytes: int) -> bool:
        """Return True if the target directory's filesystem has enough free space."""
        return free_space_bytes(directory) >= required_bytes

    def delete(self, path: Path) -> bool:
        """Delete a downloaded file. Returns True if a file was removed."""
        removed = delete_file(path)
        if removed:
            _logger.info("Deleted file: %s", path)
        else:
            _logger.warning("Attempted to delete missing file: %s", path)
        return removed

    def reveal_in_file_manager(self, path: Path) -> None:
        """Open the OS file manager with the given file selected, or its parent folder if it's a directory."""
        if not path.exists():
            _logger.warning("Cannot reveal missing path: %s", path)
            return
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(path)], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path if path.is_dir() else path.parent)], check=False)
        except OSError as error:
            _logger.error("Failed to open file manager for %s: %s", path, error)
