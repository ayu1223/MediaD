from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.logger import get_logger
from app.core.paths import get_project_root

_logger = get_logger(__name__)


class Theme(Enum):
    """Available application themes."""

    DARK = "dark"
    LIGHT = "light"


def _stylesheet_path(theme: Theme) -> Path:
    return get_project_root() / "resources" / "themes" / f"{theme.value}.qss"


def load_stylesheet(theme: Theme) -> str:
    """Return the QSS contents for the given theme, or an empty string if not yet authored."""
    path = _stylesheet_path(theme)
    if not path.exists():
        _logger.warning("Stylesheet for theme '%s' not found at %s; using default Qt styling.", theme.value, path)
        return ""
    return path.read_text(encoding="utf-8")


def apply_theme(app: QApplication, theme: Theme) -> None:
    """Apply the given theme's stylesheet to the running application."""
    app.setStyleSheet(load_stylesheet(theme))
    _logger.info("Applied '%s' theme.", theme.value)


def theme_from_value(value: str) -> Theme:
    """Resolve a stored config string into a Theme, defaulting to DARK if unrecognized."""
    try:
        return Theme(value)
    except ValueError:
        _logger.warning("Unknown theme value '%s'; defaulting to dark.", value)
        return Theme.DARK
