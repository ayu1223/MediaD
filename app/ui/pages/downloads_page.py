"""Downloads page — stat cards + live download cards.

Visual design migrated from the Fluxe UI prototype; wiring is new and connects to
the real DownloadService queue (progress, completion, failure, cancellation).

Note: the backend (DownloadManager) currently only supports cancellation, not
true pause/resume, even though DownloadStatus.PAUSED exists as an enum value.
The Pause/Resume buttons are kept for visual parity with the prototype but are
disabled with an explanatory tooltip rather than silently doing nothing — see
the backend audit notes (Issue 5) for what a real implementation would need.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from app.models.download_item import DownloadItem, DownloadStatus
from app.services.download_service import DownloadService
from app.utils.formatter import format_bytes, format_eta, format_speed
from ..components.buttons import GhostButton, IconButton
from ..components.cards import GlassCard, StatCard
from ..components.helpers import gradient_pixmap
from ..components.misc import EmptyState, StatusBadge
from ..theme import ACCENT, PRIMARY, SECONDARY, TEXT, TEXT_MUTED

_GRADIENTS = ([PRIMARY, ACCENT], [SECONDARY, PRIMARY], [ACCENT, SECONDARY])
_STATUS_LABELS = {
    DownloadStatus.QUEUED: "Queued",
    DownloadStatus.DOWNLOADING: "Downloading",
    DownloadStatus.MERGING: "Downloading",
    DownloadStatus.PAUSED: "Paused",
    DownloadStatus.COMPLETED: "Completed",
    DownloadStatus.FAILED: "Failed",
    DownloadStatus.CANCELLED: "Failed",
}


class DownloadCard(GlassCard):
    def __init__(self, item: DownloadItem, on_cancel, parent=None):
        super().__init__(parent, elevated=False, padding=18)
        self._layout.setSpacing(12)
        self._item_id = item.id
        self._on_cancel = on_cancel

        top = QHBoxLayout()
        top.setSpacing(16)

        thumb = QLabel()
        thumb.setPixmap(gradient_pixmap(140, 84, _GRADIENTS[hash(item.id) % len(_GRADIENTS)], radius=12))
        thumb.setFixedSize(140, 84)
        top.addWidget(thumb)

        info = QVBoxLayout()
        info.setSpacing(2)

        self._title_lbl = QLabel(item.media_info.title)
        self._title_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 15px;")
        self._title_lbl.setWordWrap(True)
        info.addWidget(self._title_lbl)

        self._meta_lbl = QLabel()
        self._meta_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        info.addWidget(self._meta_lbl)

        info.addSpacing(6)

        meta = QHBoxLayout()
        meta.setSpacing(14)
        self._speed_lbl = QLabel()
        self._speed_lbl.setStyleSheet("color: #56D8FF; font-weight: 600; font-size: 12px;")
        meta.addWidget(self._speed_lbl)
        self._eta_lbl = QLabel()
        self._eta_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        meta.addWidget(self._eta_lbl)
        self._pct_lbl = QLabel()
        self._pct_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: 600;")
        meta.addWidget(self._pct_lbl)
        meta.addStretch()
        self._badge = StatusBadge(_STATUS_LABELS.get(item.status, "Queued"))
        meta.addWidget(self._badge)
        info.addLayout(meta)

        from PySide6.QtWidgets import QProgressBar
        self._progress = QProgressBar()
        self._progress.setObjectName("ModernProgress")
        self._progress.setRange(0, 100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        info.addWidget(self._progress)

        top.addLayout(info, 1)

        controls = QVBoxLayout()
        controls.setSpacing(8)
        pause_btn = IconButton("fa6s.pause", "Pause (not yet supported)")
        pause_btn.setEnabled(False)
        resume_btn = IconButton("fa6s.play", "Resume (not yet supported)")
        resume_btn.setEnabled(False)
        self._cancel_btn = IconButton("fa6s.xmark", "Cancel")
        self._cancel_btn.clicked.connect(lambda: self._on_cancel(self._item_id))
        controls.addWidget(pause_btn)
        controls.addWidget(resume_btn)
        controls.addWidget(self._cancel_btn)
        top.addLayout(controls)

        wrap = QWidget()
        wrap.setLayout(top)
        self._layout.addWidget(wrap)

        self.update_from_item(item)

    def item_id(self) -> str:
        return self._item_id

    def update_from_item(self, item: DownloadItem) -> None:
        self._meta_lbl.setText(f"{item.media_info.uploader or item.media_info.provider}  ·  {item.quality}")
        self._progress.setValue(int(item.progress_percent))
        self._badge._apply(_STATUS_LABELS.get(item.status, "Queued"))
        self._pct_lbl.setText(f"{item.progress_percent:.0f}%")
        if item.is_active():
            self._speed_lbl.setText(f"↑  {format_speed(item.speed_bytes_per_sec)}")
            self._eta_lbl.setText(f"ETA  {format_eta(item.eta_seconds)}")
        else:
            self._speed_lbl.setText("")
            self._eta_lbl.setText(format_bytes(item.total_bytes) if item.total_bytes else "")
        self._cancel_btn.setEnabled(not item.is_finished())


class DownloadsPage(QWidget):
    def __init__(self, download_service: DownloadService, parent=None) -> None:
        super().__init__(parent)
        self._download_service = download_service
        self._cards: dict[str, DownloadCard] = {}

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 32)
        outer.setSpacing(22)

        title = QLabel("Downloads")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("Manage active transfers and keep an eye on what's next.")
        sub.setObjectName("PageSubtitle")
        outer.addWidget(sub)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        self._active_stat = StatCard("Active", "0", "Downloading", "fa6s.download", PRIMARY)
        self._queued_stat = StatCard("Queued", "0", "Waiting", "fa6s.layer-group", SECONDARY)
        self._done_stat = StatCard("Completed", "0", "This session", "fa6s.circle-check", ACCENT)
        self._failed_stat = StatCard("Failed", "0", "This session", "fa6s.triangle-exclamation", "#F87171")
        for i, card in enumerate((self._active_stat, self._queued_stat, self._done_stat, self._failed_stat)):
            grid.addWidget(card, 0, i)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        outer.addLayout(grid)

        head = QHBoxLayout()
        h = QLabel("Active")
        h.setObjectName("SectionHeader")
        head.addWidget(h)
        head.addStretch()
        clear_btn = GhostButton("Clear completed", icon_name="fa6s.broom")
        clear_btn.clicked.connect(self._on_clear_completed)
        head.addWidget(clear_btn)
        outer.addLayout(head)

        self._empty_state = EmptyState(
            "No downloads yet", "Fetch a URL from the Home tab to get started.", "fa6s.download"
        )
        outer.addWidget(self._empty_state)

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(14)
        outer.addLayout(self._cards_layout)

        outer.addStretch()
        scroll.setWidget(content)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

        self._download_service.progress.connect(self._on_item_upserted)
        self._download_service.item_completed.connect(self._on_item_upserted)
        self._download_service.item_failed.connect(lambda item, _msg: self._on_item_upserted(item))
        self._download_service.queue_changed.connect(self._refresh)

        self._refresh()

    def _on_item_upserted(self, item: DownloadItem) -> None:
        card = self._cards.get(item.id)
        if card is not None:
            card.update_from_item(item)
        else:
            self._refresh()
        self._update_stats()

    def _on_clear_completed(self) -> None:
        self._download_service.clear_finished()

    def _refresh(self) -> None:
        items = self._download_service.list_queue()
        existing_ids = {item.id for item in items}
        for stale_id in list(self._cards):
            if stale_id not in existing_ids:
                card = self._cards.pop(stale_id)
                self._cards_layout.removeWidget(card)
                card.deleteLater()

        for item in items:
            card = self._cards.get(item.id)
            if card is None:
                card = DownloadCard(item, on_cancel=self._download_service.cancel_download)
                self._cards[item.id] = card
                self._cards_layout.addWidget(card)
            else:
                card.update_from_item(item)

        self._empty_state.setVisible(not items)
        self._update_stats()

    def _update_stats(self) -> None:
        items = self._download_service.list_queue()
        active = sum(1 for i in items if i.is_active())
        queued = sum(1 for i in items if i.status == DownloadStatus.QUEUED)
        done = sum(1 for i in items if i.status == DownloadStatus.COMPLETED)
        failed = sum(1 for i in items if i.status in (DownloadStatus.FAILED, DownloadStatus.CANCELLED))
        self._set_value(self._active_stat, str(active))
        self._set_value(self._queued_stat, str(queued))
        self._set_value(self._done_stat, str(done))
        self._set_value(self._failed_stat, str(failed))

    @staticmethod
    def _set_value(card: StatCard, value: str) -> None:
        for label in card.findChildren(QLabel):
            if label.objectName() == "BigNumber":
                label.setText(value)
                return
