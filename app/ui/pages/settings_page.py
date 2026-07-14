"""Settings page — grouped cards, wired to the real AppSettings model.

Visual design migrated from the Fluxe UI prototype. Every control that maps to a
real AppSettings field is fully wired and persists via SettingsService.update().
A few controls from the prototype (accent color swatches, bandwidth limit,
low-power mode, release channel) have no equivalent in AppSettings — rather than
inventing new backend fields (out of scope for a UI migration), these are kept
for visual parity but disabled with a tooltip explaining they're not yet wired.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSlider, QVBoxLayout, QWidget,
)
import qtawesome as qta

from app.core.constants import SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_QUALITIES
from app.services.settings_service import SettingsService
from app.services.update_service import UpdateService
from ..components.buttons import IconButton, SecondaryButton
from ..components.cards import GlassCard
from ..components.inputs import ModernComboBox, ModernLineEdit, ModernSwitch
from ..theme import ACCENT, DANGER, PRIMARY, SECONDARY, SUCCESS, TEXT, TEXT_MUTED, WARNING

_NOT_WIRED_TOOLTIP = "Not yet configurable — no backend setting exists for this yet."


class SettingRow(QWidget):
    def __init__(self, title: str, description: str, control: QWidget, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(20)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 14px;")
        d = QLabel(description)
        d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        d.setWordWrap(True)
        col.addWidget(t)
        col.addWidget(d)
        lay.addLayout(col, 1)
        lay.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class SettingsGroup(GlassCard):
    def __init__(self, title: str, description: str, icon_name: str, color: str, parent=None):
        super().__init__(parent, padding=24)
        self._layout.setSpacing(6)

        h = QHBoxLayout()
        h.setSpacing(12)
        ic = QLabel()
        ic.setFixedSize(38, 38)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(f"background: {color}22; border-radius: 12px;")
        ic.setPixmap(qta.icon(icon_name, color=color).pixmap(20, 20))
        h.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(0)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-weight: 700; font-size: 16px;")
        d = QLabel(description)
        d.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        col.addWidget(t)
        col.addWidget(d)
        h.addLayout(col)
        h.addStretch()

        wrap = QWidget()
        wrap.setLayout(h)
        self._layout.addWidget(wrap)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1B2230;")
        self._layout.addWidget(sep)

    def addRow(self, title: str, description: str, control: QWidget) -> None:
        self._layout.addWidget(SettingRow(title, description, control))


class SettingsPage(QWidget):
    def __init__(self, settings_service: SettingsService, update_service: UpdateService | None = None, parent=None) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._update_service = update_service

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 32)
        outer.setSpacing(20)

        t = QLabel("Settings")
        t.setObjectName("PageTitle")
        outer.addWidget(t)
        s = QLabel("Fine-tune the app to fit the way you work.")
        s.setObjectName("PageSubtitle")
        outer.addWidget(s)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        settings = self._settings_service.get_settings()

        # ---- Downloads (folder, concurrency, default quality/format) ----
        dl = SettingsGroup("Downloads", "Where and how files are saved", "fa6s.download", PRIMARY)

        folder_row = QWidget()
        fl = QHBoxLayout(folder_row)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(8)
        self._folder_input = ModernLineEdit()
        self._folder_input.setText(settings.download_directory)
        self._folder_input.setMinimumWidth(220)
        self._folder_input.editingFinished.connect(self._save)
        browse_btn = IconButton("fa6s.folder-open", "Browse")
        browse_btn.clicked.connect(self._on_browse_clicked)
        fl.addWidget(self._folder_input)
        fl.addWidget(browse_btn)
        dl.addRow("Save folder", "Default location for new downloads.", folder_row)

        slider_row = QWidget()
        sl = QHBoxLayout(slider_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(10)
        self._concurrency_slider = QSlider(Qt.Orientation.Horizontal)
        self._concurrency_slider.setRange(1, 10)
        self._concurrency_slider.setValue(settings.max_concurrent_downloads)
        self._concurrency_slider.setFixedWidth(180)
        self._concurrency_val_lbl = QLabel(f"{settings.max_concurrent_downloads} parallel")
        self._concurrency_val_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600; min-width: 68px;")
        self._concurrency_slider.valueChanged.connect(self._on_concurrency_changed)
        sl.addWidget(self._concurrency_slider)
        sl.addWidget(self._concurrency_val_lbl)
        dl.addRow("Concurrent downloads", "How many files transfer at the same time.", slider_row)

        self._quality_combo = ModernComboBox(list(SUPPORTED_VIDEO_QUALITIES))
        self._quality_combo.setCurrentText(settings.default_video_quality)
        self._quality_combo.currentTextChanged.connect(self._save)
        dl.addRow("Default quality", "Used when a video's exact quality isn't chosen.", self._quality_combo)

        self._audio_format_combo = ModernComboBox(list(SUPPORTED_AUDIO_FORMATS))
        self._audio_format_combo.setCurrentText(settings.default_audio_format)
        self._audio_format_combo.currentTextChanged.connect(self._save)
        dl.addRow("Default audio format", "Used for audio-only downloads.", self._audio_format_combo)

        grid.addWidget(dl, 0, 0)

        # ---- Behavior (maps to confirm_before_delete / check_for_updates) ----
        behavior = SettingsGroup("Behavior", "Confirmations and update checks", "fa6s.sliders", SECONDARY)
        self._confirm_delete_switch = ModernSwitch(settings.confirm_before_delete)
        self._confirm_delete_switch.toggled.connect(self._save)
        behavior.addRow(
            "Confirm before deleting", "Ask before removing history entries or files.", self._confirm_delete_switch
        )
        self._check_updates_switch = ModernSwitch(settings.check_for_updates)
        self._check_updates_switch.toggled.connect(self._save)
        behavior.addRow(
            "Check for updates", "Check for a newer version automatically on startup.", self._check_updates_switch
        )
        grid.addWidget(behavior, 0, 1)

        # ---- Appearance (visual parity only — single dark theme, see main_window) ----
        appearance = SettingsGroup("Appearance", "Theme and accent", "fa6s.palette", ACCENT)
        theme_combo = ModernComboBox(["Dark (Default)"])
        theme_combo.setEnabled(False)
        theme_combo.setToolTip("Only one theme is available in the current UI.")
        appearance.addRow("Theme", "Choose a light or dark visual mode.", theme_combo)

        swatches = QWidget()
        swrow = QHBoxLayout(swatches)
        swrow.setContentsMargins(0, 0, 0, 0)
        swrow.setSpacing(8)
        for color in (PRIMARY, SECONDARY, ACCENT, SUCCESS, WARNING, DANGER):
            dot = QLabel()
            dot.setFixedSize(20, 20)
            dot.setStyleSheet(f"background: {color}; border-radius: 10px;")
            dot.setToolTip(_NOT_WIRED_TOOLTIP)
            swrow.addWidget(dot)
        appearance.addRow("Accent color", "Highlight buttons and interactive states.", swatches)
        grid.addWidget(appearance, 1, 0)

        # ---- Updates ----
        updates = SettingsGroup("Updates", "Keeping the app fresh", "fa6s.arrows-rotate", "#FBBF24")
        from app.core.version import APP_VERSION
        check_btn = SecondaryButton("Check now", icon_name="fa6s.arrows-rotate")
        check_btn.clicked.connect(self._on_check_updates_clicked)
        updates.addRow(f"You're on v{APP_VERSION}", "Manually check for a new release.", check_btn)
        grid.addWidget(updates, 1, 1)

        # ---- Network (cookies.txt for YouTube bot-check bypass) ----
        network = SettingsGroup("Network", "Authentication for sites that need it", "fa6s.shield-halved", "#56D8FF")
        cookies_row = QWidget()
        cl = QHBoxLayout(cookies_row)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)
        self._cookies_input = ModernLineEdit()
        self._cookies_input.setPlaceholderText("Not set — falls back to browser cookies")
        self._cookies_input.setText(settings.cookies_file)
        self._cookies_input.setMinimumWidth(220)
        self._cookies_input.editingFinished.connect(self._save)
        cookies_browse_btn = IconButton("fa6s.folder-open", "Browse")
        cookies_browse_btn.clicked.connect(self._on_cookies_browse_clicked)
        cookies_clear_btn = IconButton("fa6s.xmark", "Clear")
        cookies_clear_btn.clicked.connect(self._on_cookies_clear_clicked)
        cl.addWidget(self._cookies_input)
        cl.addWidget(cookies_browse_btn)
        cl.addWidget(cookies_clear_btn)
        network.addRow(
            "Cookies file",
            "A cookies.txt exported from a logged-in browser session. Used when "
            "YouTube requests bot verification and no browser cookie source is "
            "available (e.g. Chrome is running and its cookie database is locked).",
            cookies_row,
        )
        grid.addWidget(network, 2, 0, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)

        outer.addStretch()
        scroll.setWidget(content)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

    def _on_browse_clicked(self) -> None:
        current = self._folder_input.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose download folder", current)
        if selected:
            self._folder_input.setText(selected)
            self._save()

    def _on_cookies_browse_clicked(self) -> None:
        current_dir = str(Path(self._cookies_input.text()).parent) if self._cookies_input.text() else str(Path.home())
        selected, _filter = QFileDialog.getOpenFileName(
            self, "Choose cookies.txt", current_dir, "Text files (*.txt);;All files (*)"
        )
        if selected:
            self._cookies_input.setText(selected)
            self._save()

    def _on_cookies_clear_clicked(self) -> None:
        self._cookies_input.clear()
        self._save()

    def _on_concurrency_changed(self, value: int) -> None:
        self._concurrency_val_lbl.setText(f"{value} parallel")
        self._save()

    def _on_check_updates_clicked(self) -> None:
        if self._update_service is not None:
            self._update_service.check_for_updates_async()

    def _save(self, *_args: object) -> None:
        self._settings_service.update(
            download_directory=self._folder_input.text(),
            max_concurrent_downloads=self._concurrency_slider.value(),
            default_video_quality=self._quality_combo.currentText(),
            default_audio_format=self._audio_format_combo.currentText(),
            confirm_before_delete=self._confirm_delete_switch.isChecked(),
            check_for_updates=self._check_updates_switch.isChecked(),
            cookies_file=self._cookies_input.text().strip(),
        )
