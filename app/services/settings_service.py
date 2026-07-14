from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.core.config import ConfigManager
from app.core.logger import get_logger
from app.core.paths import get_default_download_dir
from app.models.settings import AppSettings

_logger = get_logger(__name__)


class SettingsService(QObject):
    """UI-facing service for reading and persisting application settings."""

    settings_changed = Signal(object)

    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        super().__init__()
        self._config_manager = config_manager or ConfigManager()
        self._settings = self._load()

    def _load(self) -> AppSettings:
        settings = AppSettings.from_dict(self._config_manager.load())
        if not settings.download_directory:
            settings.download_directory = str(get_default_download_dir())
        return settings

    def get_settings(self) -> AppSettings:
        """Return the current in-memory settings."""
        return self._settings

    def save_settings(self, settings: AppSettings) -> None:
        """Persist new settings and notify subscribers."""
        self._settings = settings
        self._config_manager.save(settings.to_dict())
        _logger.info("Settings saved.")
        self.settings_changed.emit(self._settings)

    def update(self, **changes: object) -> AppSettings:
        """Apply partial updates to the current settings and persist the result."""
        current = self._settings.to_dict()
        current.update(changes)
        updated = AppSettings.from_dict(current)
        self.save_settings(updated)
        return updated
