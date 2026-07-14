"""Home / Dashboard page: URL input + folder card + media preview.

Visual design migrated from the Fluxe UI prototype; wiring is new and connects to
the real DownloadService, ThumbnailService, and FileService.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from app.core.logger import get_logger
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo
from app.services.download_service import DownloadService
from app.services.file_service import FileService
from app.services.thumbnail_service import ThumbnailService
from app.workers.thumbnail_worker import ThumbnailWorker
from ..components.buttons import ChipButton, IconButton, PrimaryButton, SecondaryButton
from ..components.cards import GlassCard, StatCard
from ..components.helpers import gradient_pixmap
from ..components.inputs import ModernComboBox, ModernLineEdit, ModernSwitch
from ..theme import ACCENT, PRIMARY, SECONDARY, TEXT, TEXT_MUTED

_logger = get_logger(__name__)


class MediaPreviewCard(GlassCard):
    """Shows fetched media metadata and lets the user configure + trigger a download."""

    download_requested = Signal(str, bool, object)  # quality, audio_only, audio_format

    def __init__(self, parent=None):
        super().__init__(parent, elevated=True, padding=22)
        self._layout.setSpacing(18)
        self._audio_formats: list[str] = []
        self._video_qualities: list[str] = []

        row = QHBoxLayout()
        row.setSpacing(20)

        self.thumb = QLabel()
        self.thumb.setPixmap(gradient_pixmap(320, 190, [PRIMARY, ACCENT], radius=18))
        self.thumb.setFixedSize(320, 190)
        self.thumb.setScaledContents(True)
        row.addWidget(self.thumb, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)

        self.title_lbl = QLabel("Paste a URL and hit Fetch to see it here")
        self.title_lbl.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        self.title_lbl.setWordWrap(True)
        info.addWidget(self.title_lbl)

        self.by_lbl = QLabel("")
        self.by_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        info.addWidget(self.by_lbl)

        self._meta_row = QHBoxLayout()
        self._meta_row.setSpacing(8)
        self._meta_row.addStretch()
        info.addLayout(self._meta_row)

        info.addSpacing(6)

        qrow = QHBoxLayout()
        qrow.setSpacing(12)
        qlabel = QLabel("Quality")
        qlabel.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        qrow.addWidget(qlabel)
        self.quality = ModernComboBox()
        qrow.addWidget(self.quality)
        qrow.addSpacing(14)
        alabel = QLabel("Audio only")
        alabel.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        qrow.addWidget(alabel)
        self.audio_switch = ModernSwitch(False)
        self.audio_switch.toggled.connect(self._on_audio_only_toggled)
        qrow.addWidget(self.audio_switch)
        qrow.addStretch()
        info.addLayout(qrow)

        info.addSpacing(4)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.download_btn = PrimaryButton("Download", icon_name="fa6s.download")
        self.download_btn.setMinimumWidth(160)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._emit_download_requested)
        actions.addWidget(self.download_btn)
        self.queue_btn = SecondaryButton("Add to Queue", icon_name="fa6s.layer-group")
        self.queue_btn.setEnabled(False)
        self.queue_btn.clicked.connect(self._emit_download_requested)
        actions.addWidget(self.queue_btn)
        actions.addStretch()
        info.addLayout(actions)

        info.addStretch()
        row.addLayout(info, 1)

        wrap = QWidget()
        wrap.setLayout(row)
        self._layout.addWidget(wrap)

        self.setVisible(True)  # the card itself is always present; content toggles

    def _on_audio_only_toggled(self, checked: bool) -> None:
        self._populate_quality(audio_only=checked)

    def _clear_meta_row(self) -> None:
        while self._meta_row.count() > 1:  # keep the trailing stretch
            item = self._meta_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @staticmethod
    def _union_qualities(entries: list[MediaInfo]) -> list[str]:
        """Union of every entry's available_qualities, deduplicated and sorted
        descending by resolution (see class docstring / Task 2 comment above)."""
        seen: set[int] = set()
        for entry in entries:
            for quality in entry.available_qualities:
                digits = "".join(char for char in quality if char.isdigit())
                if digits:
                    seen.add(int(digits))
        return [f"{height}p" for height in sorted(seen, reverse=True)]

    def _populate_quality(self, audio_only: bool) -> None:
        self.quality.clear()
        if audio_only:
            self.quality.addItems(self._audio_formats or ["mp3"])
        else:
            self.quality.addItems(self._video_qualities or ["best"])

    def show_media(self, info: MediaInfo | PlaylistInfo) -> None:
        self._clear_meta_row()
        self.title_lbl.setText(info.title)
        self.thumb.setPixmap(gradient_pixmap(320, 190, [PRIMARY, ACCENT], radius=18))

        if isinstance(info, PlaylistInfo):
            self.by_lbl.setText("Playlist")
            # Task 2: expose real quality options for playlists instead of a
            # hardcoded "best" placeholder. Different entries in a playlist can
            # have different available resolutions, so we take the *union* of
            # every entry's available_qualities rather than only the common
            # subset, maximizing user choice. Entries lacking the selected
            # resolution simply fall back to their own best available quality
            # at download time (see _build_format_selector's height<=N
            # selector, which already degrades gracefully).
            self._video_qualities = self._union_qualities(info.entries) or ["best"]
            self._audio_formats = []
            for text in (f"{info.entry_count} videos",):
                chip = ChipButton(text)
                chip.setEnabled(False)
                self._meta_row.insertWidget(self._meta_row.count() - 1, chip)
        else:
            self.by_lbl.setText(f"by  {info.uploader}" if info.uploader else "")
            self._video_qualities = info.available_qualities or ["best"]
            self._audio_formats = info.available_audio_formats or ["mp3"]
            for text in filter(None, [info.display_duration(), info.provider.capitalize()]):
                chip = ChipButton(text)
                chip.setEnabled(False)
                self._meta_row.insertWidget(self._meta_row.count() - 1, chip)

        self.audio_switch.setChecked(False)
        self._populate_quality(audio_only=False)
        self.download_btn.setEnabled(True)
        self.queue_btn.setEnabled(True)

    def set_thumbnail_path(self, path: Path) -> None:
        from PySide6.QtGui import QPixmap

        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            self.thumb.setPixmap(pixmap)

    def clear(self) -> None:
        self._clear_meta_row()
        self.title_lbl.setText("Paste a URL and hit Fetch to see it here")
        self.by_lbl.setText("")
        self.thumb.setPixmap(gradient_pixmap(320, 190, [PRIMARY, ACCENT], radius=18))
        self.download_btn.setEnabled(False)
        self.queue_btn.setEnabled(False)

    def _emit_download_requested(self) -> None:
        audio_only = self.audio_switch.isChecked()
        quality = self.quality.currentText() or "best"
        audio_format = self.quality.currentText() if audio_only else None
        self.download_requested.emit(quality, audio_only, audio_format)


class HomePage(QWidget):
    playlist_fetched = Signal(object)

    def __init__(
        self,
        download_service: DownloadService,
        thumbnail_service: ThumbnailService,
        default_download_dir: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._download_service = download_service
        self._thumbnail_service = thumbnail_service
        self._file_service = FileService()
        self._current_media: MediaInfo | PlaylistInfo | None = None
        self._thumbnail_worker: ThumbnailWorker | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(22)

        title = QLabel("Welcome back")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        sub = QLabel("Paste a link, tweak your options and we'll handle the rest.")
        sub.setObjectName("PageSubtitle")
        outer.addWidget(sub)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        url_card = GlassCard(padding=22)
        url_card.setMinimumHeight(150)
        h = QLabel("Media URL")
        h.setObjectName("SectionHeader")
        url_card.layout().addWidget(h)
        sub2 = QLabel("Paste a video, playlist or channel URL to fetch metadata.")
        sub2.setObjectName("MutedLabel")
        url_card.layout().addWidget(sub2)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.url_input = ModernLineEdit("https://…", parent=url_card)
        row.addWidget(self.url_input, 1)
        self.fetch_btn = PrimaryButton("Fetch", icon_name="fa6s.wand-magic-sparkles")
        self.fetch_btn.setMinimumWidth(130)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        self.url_input.returnPressed.connect(self._on_fetch_clicked)
        row.addWidget(self.fetch_btn)
        row_wrap = QWidget()
        row_wrap.setLayout(row)
        url_card.layout().addWidget(row_wrap)
        grid.addWidget(url_card, 0, 0)

        folder_card = GlassCard(padding=22)
        folder_card.setMinimumHeight(150)
        fh = QLabel("Save to")
        fh.setObjectName("SectionHeader")
        folder_card.layout().addWidget(fh)
        fsub = QLabel("Downloads land in this folder unless overridden.")
        fsub.setObjectName("MutedLabel")
        folder_card.layout().addWidget(fsub)

        frow = QHBoxLayout()
        frow.setSpacing(10)
        self.folder_input = ModernLineEdit(parent=folder_card)
        self.folder_input.setText(default_download_dir)
        frow.addWidget(self.folder_input, 1)
        self.folder_btn = IconButton("fa6s.folder-open", tooltip="Browse")
        self.folder_btn.setFixedSize(46, 46)
        self.folder_btn.clicked.connect(self._on_browse_clicked)
        frow.addWidget(self.folder_btn)
        frow_wrap = QWidget()
        frow_wrap.setLayout(frow)
        folder_card.layout().addWidget(frow_wrap)
        grid.addWidget(folder_card, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)

        self._preview_card = MediaPreviewCard()
        self._preview_card.download_requested.connect(self._on_download_requested)
        outer.addWidget(self._preview_card)

        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(16)
        self._queued_stat = StatCard("Queued", "0", "Waiting", "fa6s.layer-group", PRIMARY)
        self._week_stat = StatCard("This week", "0", "Downloads", "fa6s.calendar", SECONDARY)
        self._rate_stat = StatCard("Success rate", "—", "Last 30 days", "fa6s.chart-line", ACCENT)
        for card in (self._queued_stat, self._week_stat, self._rate_stat):
            self._stats_row.addWidget(card)
        outer.addLayout(self._stats_row)

        outer.addStretch()
        scroll.setWidget(content)

        wrap = QVBoxLayout(self)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.addWidget(scroll)

        self._download_service.metadata_ready.connect(self._on_metadata_ready)
        self._download_service.metadata_failed.connect(self._on_metadata_failed)
        self._download_service.queue_changed.connect(self._refresh_stats)
        self._refresh_stats()

    # ------------------------------------------------------------------

    def _on_fetch_clicked(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        self._preview_card.clear()
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Fetching…")
        self._download_service.fetch_metadata(url)

    def _on_browse_clicked(self) -> None:
        current = self.folder_input.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose download folder", current)
        if selected:
            self.folder_input.setText(selected)

    def _on_metadata_ready(self, media) -> None:
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch")
        self._current_media = media
        self._preview_card.show_media(media)
        if isinstance(media, PlaylistInfo):
            self.playlist_fetched.emit(media)

        thumbnail_url = media.thumbnail_url
        if thumbnail_url:
            cached = self._thumbnail_service.get_cached_path(thumbnail_url)
            if cached is not None:
                self._preview_card.set_thumbnail_path(cached)
            else:
                self._thumbnail_worker = ThumbnailWorker(thumbnail_url, self._thumbnail_service, parent=self)
                self._thumbnail_worker.finished_ok.connect(self._on_thumbnail_ready)
                self._thumbnail_worker.finished.connect(self._thumbnail_worker.deleteLater)
                self._thumbnail_worker.start()

    def _on_metadata_failed(self, message: str) -> None:
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch")
        _logger.warning("Metadata fetch failed: %s", message)

    def _on_thumbnail_ready(self, url: str, path) -> None:
        if self._current_media and self._current_media.thumbnail_url == url:
            self._preview_card.set_thumbnail_path(path)

    def _on_download_requested(self, quality: str, audio_only: bool, audio_format: str | None) -> None:
        if self._current_media is None:
            return
        destination_dir = Path(self.folder_input.text())

        if isinstance(self._current_media, PlaylistInfo):
            self._download_service.enqueue_playlist(
                self._current_media, destination_dir, quality, audio_only, audio_format
            )
        else:
            known_extension = self._current_media.extra.get("extension")
            extension = known_extension or ((audio_format or "mp3") if audio_only else "mkv")
            destination_path = self._file_service.build_destination_path(
                destination_dir, Path(self._current_media.title).stem, extension
            )
            self._download_service.enqueue_download(
                self._current_media, destination_path, quality, audio_only, audio_format
            )

    def _refresh_stats(self) -> None:
        items = self._download_service.list_queue()
        queued = sum(1 for i in items if not i.is_active() and i.progress_percent < 100)
        self._set_stat_value(self._queued_stat, str(queued))

    @staticmethod
    def _set_stat_value(card: StatCard, value: str) -> None:
        for label in card.findChildren(QLabel):
            if label.objectName() == "BigNumber":
                label.setText(value)
                return
