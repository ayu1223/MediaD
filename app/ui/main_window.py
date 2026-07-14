from __future__ import annotations

import json
from datetime import datetime, timezone

from PySide6.QtCore import QByteArray, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH
from app.core.logger import get_logger
from app.core.signals import get_signal_bus
from app.core.version import APP_NAME, APP_VERSION
from app.database.database import Database
from app.database.history_repository import HistoryRepository
from app.database.settings_repository import SettingsRepository
from app.models.download_item import DownloadItem
from app.models.history_item import HistoryItem, MediaType
from app.services.download_service import DownloadService
from app.services.history_service import HistoryService
from app.services.settings_service import SettingsService
from app.services.thumbnail_service import ThumbnailService
from app.services.update_service import UpdateService
from app.ui.components.misc import ToastHost
from app.ui.components.sidebar import Sidebar
from app.ui.components.status_bar import StatusBar
from app.ui.components.topbar import TopBar
from app.ui.dialogs.confirm_dialog import confirm
from app.ui.pages.about_page import AboutPage
from app.ui.pages.downloads_page import DownloadsPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.home_page import HomePage
from app.ui.pages.playlist_page import PlaylistPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.theme import BG, build_stylesheet

_logger = get_logger(__name__)

_WINDOW_GEOMETRY_KEY = "window_geometry"

_PAGE_TITLES = {
    "home": "Home",
    "playlist": "Playlist",
    "downloads": "Downloads",
    "history": "History",
    "settings": "Settings",
    "about": "About",
}


class MainWindow(QMainWindow):
    """The application's composition root and top-level window.

    Owns the database, repositories, and services, and wires them into the UI
    migrated from the Fluxe design prototype. No other module constructs these
    backend objects. The visual shell (sidebar/topbar/stack/status bar) and all
    page components come from the design prototype; only the wiring here and
    inside each page is new.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(980, 640)
        self.resize(max(DEFAULT_WINDOW_WIDTH, 980), max(DEFAULT_WINDOW_HEIGHT, 640))
        self.setStyleSheet(build_stylesheet())

        self._database = Database()
        self._settings_repository = SettingsRepository(self._database)
        self._history_repository = HistoryRepository(self._database)

        self._settings_service = SettingsService()
        settings = self._settings_service.get_settings()

        self._history_service = HistoryService(self._history_repository)
        self._download_service = DownloadService(
            max_concurrent_downloads=settings.max_concurrent_downloads,
            cookies_file=settings.cookies_file or None,
        )
        self._thumbnail_service = ThumbnailService()
        self._update_service = UpdateService()

        root = QWidget(self)
        root.setObjectName("RootBackground")
        root.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(root)

        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigated.connect(self.navigate)
        h.addWidget(self.sidebar)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.topbar = TopBar()
        self.topbar.sidebarToggle.connect(self.sidebar.toggleCollapsed)
        self.topbar.settingsRequested.connect(lambda: self.navigate("settings"))
        rl.addWidget(self.topbar)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.stack, 1)

        self._home_page = HomePage(self._download_service, self._thumbnail_service, settings.download_directory)
        self._playlist_page = PlaylistPage(self._download_service, settings.download_directory)
        self._downloads_page = DownloadsPage(self._download_service)
        self._history_page = HistoryPage(self._history_service, confirm_fn=self._confirm)
        self._settings_page = SettingsPage(self._settings_service, self._update_service)
        self._about_page = AboutPage(self)

        self.pages: dict[str, QWidget] = {
            "home": self._home_page,
            "playlist": self._playlist_page,
            "downloads": self._downloads_page,
            "history": self._history_page,
            "settings": self._settings_page,
            "about": self._about_page,
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        toast_wrap = QWidget()
        tw = QHBoxLayout(toast_wrap)
        tw.setContentsMargins(20, 0, 20, 8)
        tw.addStretch()
        self.toast_host = ToastHost()
        tw.addWidget(self.toast_host)
        rl.addWidget(toast_wrap)

        status_wrap = QWidget()
        sw = QHBoxLayout(status_wrap)
        sw.setContentsMargins(20, 6, 20, 14)
        sw.setSpacing(0)
        self.status = StatusBar()
        sw.addWidget(self.status)
        rl.addWidget(status_wrap)

        h.addWidget(right, 1)

        # Per-page fade-in: the effect is created fresh for whichever page is
        # entering and removed again once the fade completes, rather than living
        # permanently on the stack. A persistent stack-level QGraphicsOpacityEffect
        # was found to cause continuous "QPainter: paint device can only be painted
        # by one painter at a time" warnings once real, continuously-updating
        # widgets (progress bars, pulsing status dot) are added to the pages.
        self._fade_anim: QPropertyAnimation | None = None
        self._fade_target: QWidget | None = None
        self._had_pending_downloads = False

        self._connect_backend_signals()
        self._restore_geometry()

        self.navigate("home")

        if settings.check_for_updates:
            self._update_service.check_for_updates_async()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _finish_fade(self) -> None:
        if self._fade_target is not None:
            self._fade_target.setGraphicsEffect(None)
        self._fade_target = None

    def navigate(self, key: str) -> None:
        widget = self.pages.get(key)
        if widget is None:
            return
        if self.stack.currentWidget() is not widget:
            if self._fade_anim is not None:
                self._fade_anim.stop()
                self._finish_fade()

            self.stack.setCurrentWidget(widget)

            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.finished.connect(self._finish_fade)

            self._fade_target = widget
            self._fade_anim = anim
            anim.start()

        self.sidebar.setActive(key)
        self.topbar.setSectionTitle(_PAGE_TITLES.get(key, key.title()))

    # ------------------------------------------------------------------
    # Backend wiring
    # ------------------------------------------------------------------

    def _connect_backend_signals(self) -> None:
        bus = get_signal_bus()
        bus.status_message.connect(self._on_status_message)
        bus.error_occurred.connect(self._on_bus_error)

        self._home_page.playlist_fetched.connect(self._on_playlist_fetched)

        self._download_service.queue_changed.connect(self._on_queue_changed)
        self._download_service.progress.connect(self._on_queue_changed)
        self._download_service.item_started.connect(self._on_item_started)
        self._download_service.item_completed.connect(self._on_item_completed)
        self._download_service.item_cancelled.connect(self._on_item_cancelled)
        self._download_service.item_failed.connect(self._on_item_failed)
        self._download_service.metadata_failed.connect(self._on_metadata_failed)

        self._settings_service.settings_changed.connect(self._on_settings_changed)

        self._update_service.check_finished.connect(self._on_update_check_finished)

        self._on_queue_changed()

    def _confirm(self, title: str, message: str) -> bool:
        if not self._settings_service.get_settings().confirm_before_delete:
            return True
        return confirm(self, title, message)

    def _on_playlist_fetched(self, playlist: object) -> None:
        self._playlist_page.load_playlist(playlist)  # type: ignore[arg-type]
        get_signal_bus().status_message.emit(
            f"Playlist '{getattr(playlist, 'title', '')}' loaded — see the Playlist tab to pick items."
        )
        self.navigate("playlist")

    def _on_queue_changed(self, *_args: object) -> None:
        items = self._download_service.list_queue()
        active = [item for item in items if item.is_active()]
        total_speed = sum(item.speed_bytes_per_sec for item in active)
        if active:
            speed_mb = total_speed / (1024 * 1024)
            self.status.setStatus("Downloading", f"{len(active)} active · {speed_mb:.1f} MB/s", "#7C5CFF")
        else:
            self.status.setStatus("Ready", "No active downloads", "#4ADE80")

        # Task 5: "Queue finished" notification. Fires once, the moment the last
        # active download drains with nothing left queued behind it — not on
        # every empty-queue check (e.g. at startup, before anything was ever
        # queued).
        has_pending_or_active = bool(active) or any(not item.is_finished() for item in items)
        if self._had_pending_downloads and not has_pending_or_active:
            self.toast_host.notify("Queue finished — all downloads are done.", "success")
        self._had_pending_downloads = has_pending_or_active

    def _on_item_started(self, item: DownloadItem) -> None:
        self.toast_host.notify(f"Download started: {item.media_info.title}", "info")

    def _on_item_completed(self, item: DownloadItem) -> None:
        history_item = HistoryItem(
            id=item.id,
            title=item.media_info.title,
            provider=item.media_info.provider,
            source_url=item.media_info.source_url,
            file_path=item.destination_path,
            media_type=MediaType.AUDIO if item.audio_only else MediaType.VIDEO,
            quality=item.quality,
            file_size_bytes=item.total_bytes,
            completed_at=datetime.now(timezone.utc),
            thumbnail_url=item.media_info.thumbnail_url,
        )
        self._history_service.add(history_item)
        self._history_page.refresh()
        self.toast_host.notify(f"Download completed: {item.media_info.title}", "success")
        self._on_queue_changed()

    def _on_item_cancelled(self, item: DownloadItem) -> None:
        self.toast_host.notify(f"Cancelled: {item.media_info.title}", "info")
        self._on_queue_changed()

    def _on_item_failed(self, item: DownloadItem, message: str) -> None:
        get_signal_bus().error_occurred.emit(item.media_info.title, message)
        self._on_queue_changed()

    def _on_metadata_failed(self, message: str) -> None:
        get_signal_bus().error_occurred.emit("Fetch failed", message)

    def _on_status_message(self, message: str) -> None:
        # Task 5: transient informational messages (e.g. "Playlist loaded", "A new
        # version is available") are now surfaced as a real toast notification
        # rather than only being logged and silently lost on the user's end.
        _logger.info(message)
        self.toast_host.notify(message, "info")

    def _on_bus_error(self, context: str, message: str) -> None:
        self.status.setStatus("Failed", f"{context}: {message}", "#F87171")
        _logger.error("%s: %s", context, message)
        self.toast_host.notify(f"{context}: {message}", "error")

    def _on_settings_changed(self, settings: object) -> None:
        max_concurrent = getattr(settings, "max_concurrent_downloads", None)
        if max_concurrent is not None:
            self._download_service.set_max_concurrent_downloads(max_concurrent)
        cookies_file = getattr(settings, "cookies_file", None)
        self._download_service.set_cookies_file(cookies_file or None)
        # Note: the migrated UI ships a single dark theme (matching the design
        # prototype, which has no light variant), so unlike the previous UI there
        # is no stylesheet to swap here when settings.theme changes.

    def _on_update_check_finished(self, update_info: object) -> None:
        available = getattr(update_info, "update_available", False)
        latest = getattr(update_info, "latest_version", None)
        if available and latest:
            get_signal_bus().status_message.emit(f"A new version ({latest}) is available.")

    # ------------------------------------------------------------------
    # Window geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        raw = self._settings_repository.get(_WINDOW_GEOMETRY_KEY)
        if not raw:
            return
        try:
            payload = json.loads(raw)
            geometry = QByteArray.fromBase64(payload["geometry"].encode("ascii"))
            if geometry.isEmpty():
                return
            # Guard against a geometry saved by a previous version of the app with a
            # smaller minimum size: applying it as-is could hand Qt/the native window
            # manager a size below the window's current minimumSize, which is a
            # known trigger for "QWindowsWindow::setGeometry: Unable to set
            # geometry" warnings on Windows. restoreGeometry() itself clamps to the
            # *current* min/max size, but only after the fact, so we additionally
            # verify the restore actually produced a valid size and fall back
            # to the default if not.
            restored = self.restoreGeometry(geometry)
            if not restored or self.width() < self.minimumWidth() or self.height() < self.minimumHeight():
                self.resize(max(DEFAULT_WINDOW_WIDTH, 980), max(DEFAULT_WINDOW_HEIGHT, 640))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            _logger.warning("Could not restore window geometry: %s", error)

    def _save_geometry(self) -> None:
        geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        self._settings_repository.set(_WINDOW_GEOMETRY_KEY, json.dumps({"geometry": geometry}))

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_geometry()
        self._database.close()
        super().closeEvent(event)
