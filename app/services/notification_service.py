"""Issue 5: native OS notifications for download lifecycle events.

Uses QSystemTrayIcon, which is PySide6's cross-platform mechanism for this:
showMessage() routes through the native notification center on Windows and
macOS, and through the desktop's notification daemon (implementing the
freedesktop.org notification spec) on Linux — so "native OS notification" and
"tray notification" are, in practice, the same call on every platform Qt
supports. No extra dependency is needed.

This sits in the Services layer per the mandated architecture: the UI layer
(MainWindow) only ever calls NotificationService.notify(...); it does not touch
QSystemTrayIcon directly.
"""
from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QWidget

from app.core.logger import get_logger

_logger = get_logger(__name__)

_DEFAULT_TIMEOUT_MS = 6000


class NotificationService:
    """Shows native/tray notifications for significant download events.

    Silently does nothing if the current desktop environment has no system tray
    (QSystemTrayIcon.isSystemTrayAvailable() is False) or if notifications are
    disabled in settings — callers don't need to check either condition
    themselves before calling notify().
    """

    def __init__(self, parent: QWidget | None = None, icon: QIcon | None = None) -> None:
        self._enabled = True
        self._tray_icon: QSystemTrayIcon | None = None

        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = QSystemTrayIcon(parent)
            if icon is not None:
                self._tray_icon.setIcon(icon)
            self._tray_icon.setVisible(True)
        else:
            _logger.info("No system tray available on this platform; notifications will be skipped.")

    def set_enabled(self, enabled: bool) -> None:
        """Toggle notifications on/off, e.g. from a live settings change."""
        self._enabled = enabled

    def notify(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
    ) -> None:
        """Show a native/tray notification, or do nothing if disabled/unavailable."""
        if not self._enabled or self._tray_icon is None:
            return
        try:
            self._tray_icon.showMessage(title, message, icon, timeout_ms)
        except Exception as error:  # noqa: BLE001 - a failed notification must never crash the app
            _logger.warning("Failed to show notification %r: %s", title, error)