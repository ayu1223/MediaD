"""Playlist page — Spotify-style banner + video rows + floating action panel.

Visual design migrated from the Fluxe UI prototype; wiring is new and connects to
the real DownloadService.enqueue_playlist with the user's checked subset of entries.
"""
from __future__ import annotations

from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from app.core.constants import SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_QUALITIES
from app.models.playlist import PlaylistInfo
from app.services.download_service import DownloadService
from ..components.buttons import ChipButton, GhostButton, PrimaryButton, SecondaryButton
from ..components.cards import GlassCard
from ..components.helpers import gradient_pixmap, add_shadow
from ..components.inputs import ModernComboBox, ModernSwitch, SearchBox
from ..components.misc import EmptyState, StatusBadge
from ..theme import ACCENT, PRIMARY, SECONDARY, TEXT, TEXT_MUTED

_ROW_COLORS = ([PRIMARY, ACCENT], [SECONDARY, PRIMARY], [ACCENT, SECONDARY], ["#F87171", "#FBBF24"], ["#4ADE80", ACCENT])


class PlaylistBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(220)
        add_shadow(self, blur=48, y=18, alpha=120)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(24)

        self.cover = QLabel()
        self.cover.setPixmap(gradient_pixmap(180, 180, [PRIMARY, SECONDARY], radius=22, icon_name="fa6s.music"))
        self.cover.setFixedSize(180, 180)
        lay.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(6)

        kicker = QLabel("PLAYLIST")
        kicker.setStyleSheet(f"color: {ACCENT}; letter-spacing: 1.8px; font-size: 11px; font-weight: 700;")
        col.addWidget(kicker)

        self.title_lbl = QLabel("No playlist loaded")
        self.title_lbl.setStyleSheet(f"color: {TEXT}; font-size: 34px; font-weight: 800; letter-spacing: -0.5px;")
        self.title_lbl.setWordWrap(True)
        col.addWidget(self.title_lbl)

        self.by_lbl = QLabel("Fetch a playlist URL from the Home tab to populate this list.")
        self.by_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        self.by_lbl.setWordWrap(True)
        col.addWidget(self.by_lbl)

        self._meta_row = QHBoxLayout()
        self._meta_row.setSpacing(8)
        self._meta_row.addStretch()
        col.addLayout(self._meta_row)

        col.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.download_all_btn = PrimaryButton("Download All", icon_name="fa6s.download")
        self.download_all_btn.setEnabled(False)
        actions.addWidget(self.download_all_btn)
        self.select_all_btn = SecondaryButton("Select All", icon_name="fa6s.check-double")
        self.select_all_btn.setEnabled(False)
        actions.addWidget(self.select_all_btn)
        self.deselect_btn = GhostButton("Deselect", icon_name="fa6s.xmark")
        self.deselect_btn.setEnabled(False)
        actions.addWidget(self.deselect_btn)
        actions.addStretch()
        col.addLayout(actions)

        lay.addLayout(col, 1)

    def set_playlist(self, playlist: PlaylistInfo) -> None:
        self.title_lbl.setText(playlist.title)
        self.by_lbl.setText(f"{playlist.provider.capitalize()} playlist")
        while self._meta_row.count() > 1:
            item = self._meta_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        chip = ChipButton(f"{playlist.entry_count} videos")
        chip.setEnabled(False)
        self._meta_row.insertWidget(0, chip)
        for button in (self.download_all_btn, self.select_all_btn, self.deselect_btn):
            button.setEnabled(True)

    def clear(self) -> None:
        self.title_lbl.setText("No playlist loaded")
        self.by_lbl.setText("Fetch a playlist URL from the Home tab to populate this list.")
        while self._meta_row.count() > 1:
            item = self._meta_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for button in (self.download_all_btn, self.select_all_btn, self.deselect_btn):
            button.setEnabled(False)


class PlaylistRow(QFrame):
    def __init__(self, idx: int, title: str, uploader: str, duration: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "QFrame { background: transparent; border-radius: 14px; }"
            "QFrame:hover { background: rgba(255,255,255,0.03); }"
        )
        self.setMinimumHeight(76)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        lay.addWidget(self.checkbox)

        num = QLabel(f"{idx:02d}")
        num.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; min-width: 22px;")
        lay.addWidget(num)

        thumb = QLabel()
        thumb.setPixmap(gradient_pixmap(96, 56, _ROW_COLORS[(idx - 1) % len(_ROW_COLORS)], radius=10))
        thumb.setFixedSize(96, 56)
        lay.addWidget(thumb)

        info = QVBoxLayout()
        info.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 14px;")
        info.addWidget(t)
        u = QLabel(uploader)
        u.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        info.addWidget(u)
        lay.addLayout(info, 1)

        dur = QLabel(duration)
        dur.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        dur.setMinimumWidth(60)
        dur.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(dur)

        lay.addWidget(StatusBadge("Queued"))


class PlaylistPage(QWidget):
    def __init__(self, download_service: DownloadService, default_download_dir: str, parent=None) -> None:
        super().__init__(parent)
        self._download_service = download_service
        self._default_download_dir = default_download_dir
        self._playlist: PlaylistInfo | None = None
        self._rows: list[PlaylistRow] = []

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 32)
        outer.setSpacing(22)

        self._banner = PlaylistBanner()
        self._banner.download_all_btn.clicked.connect(lambda: self._select_all(True))
        self._banner.select_all_btn.clicked.connect(lambda: self._select_all(True))
        self._banner.deselect_btn.clicked.connect(lambda: self._select_all(False))
        self._banner.download_all_btn.clicked.connect(self._on_download_clicked)
        outer.addWidget(self._banner)

        self._list_card = GlassCard(padding=18)
        self._list_card.layout().setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        h = QLabel("Videos")
        h.setObjectName("SectionHeader")
        header.addWidget(h)
        header.addStretch()
        self.search = SearchBox("Search videos in this playlist…")
        self.search.setMinimumWidth(280)
        self.search.textChanged.connect(self._apply_filter)
        header.addWidget(self.search)
        hw = QWidget()
        hw.setLayout(header)
        self._list_card.layout().addWidget(hw)

        self._empty_state = EmptyState("No playlist loaded", "Fetch a playlist from the Home tab.", "fa6s.list-ul")
        self._list_card.layout().addWidget(self._empty_state)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(4)
        rows_wrap = QWidget()
        rows_wrap.setLayout(self._rows_layout)
        self._list_card.layout().addWidget(rows_wrap)

        outer.addWidget(self._list_card)

        floating = GlassCard(elevated=True, padding=18)
        fl = QHBoxLayout()
        fl.setSpacing(14)

        icon_bubble = QLabel()
        icon_bubble.setFixedSize(46, 46)
        icon_bubble.setStyleSheet("background: rgba(124,92,255,0.16); border-radius: 14px;")
        icon_bubble.setPixmap(qta.icon("fa6s.circle-check", color=PRIMARY).pixmap(22, 22))
        icon_bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(icon_bubble)

        col = QVBoxLayout()
        col.setSpacing(0)
        self._selection_lbl = QLabel("0 videos selected")
        self._selection_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 15px;")
        self._selection_sub_lbl = QLabel("Choose a quality and destination, then download.")
        self._selection_sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        col.addWidget(self._selection_lbl)
        col.addWidget(self._selection_sub_lbl)
        fl.addLayout(col)
        fl.addStretch()

        self.quality = ModernComboBox(list(SUPPORTED_VIDEO_QUALITIES))
        fl.addWidget(self.quality)
        self.audio_switch = ModernSwitch(False)
        fl.addWidget(self.audio_switch)

        self.folder_btn = SecondaryButton("Folder", icon_name="fa6s.folder-open")
        self.folder_btn.clicked.connect(self._on_browse_clicked)
        fl.addWidget(self.folder_btn)

        self.dl_btn = PrimaryButton("Download Selected", icon_name="fa6s.download")
        self.dl_btn.clicked.connect(self._on_download_clicked)
        fl.addWidget(self.dl_btn)

        wrap = QWidget()
        wrap.setLayout(fl)
        floating.layout().addWidget(wrap)
        outer.addWidget(floating)

        outer.addStretch()
        scroll.setWidget(content)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

        self._destination_dir = default_download_dir
        self._update_selection_label()

    # ------------------------------------------------------------------

    def load_playlist(self, playlist: PlaylistInfo) -> None:
        self._playlist = playlist
        self._banner.set_playlist(playlist)

        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows = []

        for i, entry in enumerate(playlist.entries, start=1):
            row = PlaylistRow(i, entry.title, entry.uploader or playlist.provider, entry.display_duration() or "—")
            row.checkbox.toggled.connect(self._update_selection_label)
            self._rows_layout.addWidget(row)
            self._rows.append(row)

        self._empty_state.setVisible(not playlist.entries)
        self._update_selection_label()

    def _apply_filter(self, query: str) -> None:
        if not self._playlist:
            return
        query = query.lower().strip()
        for row, entry in zip(self._rows, self._playlist.entries):
            row.setVisible(query in entry.title.lower() if query else True)

    def _select_all(self, checked: bool) -> None:
        for row in self._rows:
            row.checkbox.setChecked(checked)

    def _on_browse_clicked(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose download folder", self._destination_dir)
        if selected:
            self._destination_dir = selected

    def _update_selection_label(self, *_args: object) -> None:
        count = sum(1 for row in self._rows if row.checkbox.isChecked())
        self._selection_lbl.setText(f"{count} video{'s' if count != 1 else ''} selected")
        self.dl_btn.setEnabled(count > 0)

    def _on_download_clicked(self) -> None:
        if self._playlist is None:
            return
        selected_entries = [
            entry for row, entry in zip(self._rows, self._playlist.entries) if row.checkbox.isChecked()
        ]
        if not selected_entries:
            return

        quality = self.quality.currentText() or "best"
        audio_only = self.audio_switch.isChecked()
        audio_format = list(SUPPORTED_AUDIO_FORMATS)[0] if audio_only else None

        partial_playlist = PlaylistInfo(
            id=self._playlist.id,
            title=self._playlist.title,
            provider=self._playlist.provider,
            source_url=self._playlist.source_url,
            thumbnail_url=self._playlist.thumbnail_url,
            entries=selected_entries,
        )
        self._download_service.enqueue_playlist(
            partial_playlist, Path(self._destination_dir), quality, audio_only, audio_format
        )
