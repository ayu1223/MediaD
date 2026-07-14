"""History page — wired to the real HistoryService."""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.core.logger import get_logger
from app.models.history_item import HistoryItem
from app.services.history_service import HistoryService
from app.utils.formatter import format_bytes
from ..components.buttons import ChipButton, GhostButton, IconButton
from ..components.cards import GlassCard, StatCard
from ..components.helpers import gradient_pixmap
from ..components.inputs import SearchBox
from ..components.misc import EmptyState
from ..theme import ACCENT, PRIMARY, SECONDARY, TEXT

_logger = get_logger(__name__)


class HistoryCard(GlassCard):
    def __init__(self, item: HistoryItem, on_delete, parent=None):
        super().__init__(parent, padding=16)
        self._layout.setSpacing(12)
        self._item = item

        row = QHBoxLayout()
        row.setSpacing(16)

        thumb = QLabel()
        thumb.setPixmap(gradient_pixmap(150, 90, [PRIMARY, ACCENT], radius=12))
        thumb.setFixedSize(150, 90)
        row.addWidget(thumb)

        info = QVBoxLayout()
        info.setSpacing(3)
        t = QLabel(item.title)
        t.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 15px;")
        t.setWordWrap(True)
        info.addWidget(t)

        chips = QHBoxLayout()
        chips.setSpacing(6)
        size_text = format_bytes(item.file_size_bytes) if item.file_size_bytes else "—"
        for c in [item.quality, size_text, item.completed_at.strftime("%Y-%m-%d")]:
            chip = ChipButton(c)
            chip.setEnabled(False)
            chips.addWidget(chip)
        chips.addStretch()
        info.addLayout(chips)
        row.addLayout(info, 1)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        open_folder_btn = IconButton("fa6s.folder-open", "Show in folder")
        open_folder_btn.clicked.connect(self._open_folder)
        actions.addWidget(open_folder_btn)
        open_btn = IconButton("fa6s.arrow-up-right-from-square", "Open")
        open_btn.setEnabled(item.file_path.exists())
        open_btn.clicked.connect(self._open_file)
        actions.addWidget(open_btn)
        delete_btn = IconButton("fa6s.trash", "Delete")
        delete_btn.clicked.connect(lambda: on_delete(item.id))
        actions.addWidget(delete_btn)
        row.addLayout(actions)

        wrap = QWidget()
        wrap.setLayout(row)
        self._layout.addWidget(wrap)

    def _open_file(self) -> None:
        if self._item.file_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._item.file_path)))
        else:
            _logger.warning("Cannot open history item %s: file missing at %s", self._item.id, self._item.file_path)

    def _open_folder(self) -> None:
        folder = self._item.file_path.parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        else:
            _logger.warning("Cannot open folder for history item %s: %s missing", self._item.id, folder)


class HistoryPage(QWidget):
    def __init__(self, history_service: HistoryService, confirm_fn=None, parent=None) -> None:
        super().__init__(parent)
        self._history_service = history_service
        self._confirm_fn = confirm_fn

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 32)
        outer.setSpacing(22)

        row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        t = QLabel("History")
        t.setObjectName("PageTitle")
        s = QLabel("Everything you've downloaded, neatly kept.")
        s.setObjectName("PageSubtitle")
        title_col.addWidget(t)
        title_col.addWidget(s)
        row.addLayout(title_col)
        row.addStretch()

        self.search = SearchBox("Search your history…")
        self.search.setMinimumWidth(320)
        self.search.textChanged.connect(self._on_search_changed)
        row.addWidget(self.search)
        row.addSpacing(8)
        clear_btn = GhostButton("Clear all", icon_name="fa6s.broom")
        clear_btn.clicked.connect(self._on_clear_all)
        row.addWidget(clear_btn)
        outer.addLayout(row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        self._count_stat = StatCard("Items", "0", "All time", "fa6s.clock-rotate-left", PRIMARY)
        self._size_stat = StatCard("Total size", "0 B", "On disk", "fa6s.hard-drive", SECONDARY)
        for i, card in enumerate((self._count_stat, self._size_stat)):
            grid.addWidget(card, 0, i)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)

        head = QHBoxLayout()
        h = QLabel("Recent")
        h.setObjectName("SectionHeader")
        head.addWidget(h)
        head.addStretch()
        outer.addLayout(head)

        self._empty_state = EmptyState(
            "No history yet", "Completed downloads will appear here.", "fa6s.clock-rotate-left"
        )
        outer.addWidget(self._empty_state)

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(12)
        outer.addLayout(self._cards_layout)

        outer.addStretch()
        scroll.setWidget(content)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

        self.refresh()

    def _on_search_changed(self, _text: str) -> None:
        self.refresh()

    def refresh(self) -> None:
        query = self.search.text()
        items = self._history_service.search(query) if query else self._history_service.list_all()

        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for history_item in items:
            self._cards_layout.addWidget(HistoryCard(history_item, on_delete=self._delete_item))

        self._empty_state.setVisible(not items)

        all_items = self._history_service.list_all()
        self._set_value(self._count_stat, str(len(all_items)))
        total_bytes = sum(i.file_size_bytes or 0 for i in all_items)
        self._set_value(self._size_stat, format_bytes(total_bytes))

    def _delete_item(self, item_id: str) -> None:
        if self._confirm_fn and not self._confirm_fn("Delete History Entry", "Remove this entry from history?"):
            return
        self._history_service.delete(item_id)
        self.refresh()

    def _on_clear_all(self) -> None:
        if self._confirm_fn and not self._confirm_fn("Clear History", "Remove all entries from download history?"):
            return
        self._history_service.clear()
        self.refresh()

    @staticmethod
    def _set_value(card: StatCard, value: str) -> None:
        for label in card.findChildren(QLabel):
            if label.objectName() == "BigNumber":
                label.setText(value)
                return
