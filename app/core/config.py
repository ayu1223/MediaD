from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.logger import get_logger
from app.core.paths import get_config_file_path, get_config_template_path

_logger = get_logger(__name__)


class ConfigManager:
    """Loads and persists a JSON configuration file, recovering safely from corruption."""

    def __init__(self, config_path: Path | None = None, template_path: Path | None = None) -> None:
        self._config_path = config_path or get_config_file_path()
        self._template_path = template_path or get_config_template_path()

    def load(self) -> dict[str, Any]:
        """Load configuration from disk, seeding or recovering it from the default template as needed."""
        if not self._config_path.exists():
            _logger.info("No config file found at %s; creating from template.", self._config_path)
            return self._reset_from_template()

        try:
            with self._config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("Configuration root must be a JSON object.")
            return data
        except (json.JSONDecodeError, ValueError, OSError) as error:
            _logger.error("Configuration file corrupted or unreadable (%s); recovering from template.", error)
            self._quarantine_corrupted_file()
            return self._reset_from_template()

    def save(self, data: dict[str, Any]) -> None:
        """Persist configuration atomically to avoid leaving a corrupted file on crash."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._config_path.with_suffix(".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=4, sort_keys=True)
            temp_path.replace(self._config_path)
        except OSError as error:
            _logger.error("Failed to save configuration to %s: %s", self._config_path, error)
            raise

    def load_default(self) -> dict[str, Any]:
        """Return the bundled default configuration template."""
        with self._template_path.open("r", encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
        return data

    def _reset_from_template(self) -> dict[str, Any]:
        default_data = self.load_default()
        self.save(default_data)
        return default_data

    def _quarantine_corrupted_file(self) -> None:
        if not self._config_path.exists():
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = self._config_path.with_name(f"{self._config_path.stem}.corrupted-{timestamp}.json")
        try:
            shutil.move(str(self._config_path), str(backup_path))
            _logger.warning("Corrupted config backed up to %s", backup_path)
        except OSError as error:
            _logger.error("Could not back up corrupted config file: %s", error)
