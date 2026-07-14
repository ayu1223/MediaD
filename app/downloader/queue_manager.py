from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.models.download_item import DownloadItem, DownloadStatus


class QueueManager(QObject):
    """Maintains the ordered set of download items. Does not perform any I/O itself."""

    item_added = Signal(object)
    item_removed = Signal(str)
    item_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._items: dict[str, DownloadItem] = {}
        self._order: list[str] = []

    def add(self, item: DownloadItem) -> None:
        self._items[item.id] = item
        self._order.append(item.id)
        self.item_added.emit(item)

    def remove(self, item_id: str) -> None:
        if item_id in self._items:
            del self._items[item_id]
            self._order.remove(item_id)
            self.item_removed.emit(item_id)

    def get(self, item_id: str) -> DownloadItem | None:
        return self._items.get(item_id)

    def list_all(self) -> list[DownloadItem]:
        return [self._items[item_id] for item_id in self._order]

    def list_pending(self) -> list[DownloadItem]:
        return [item for item in self.list_all() if item.status == DownloadStatus.QUEUED]

    def pop_next_pending(self) -> DownloadItem | None:
        """Return the next queued item without removing it from the queue's history."""
        for item_id in self._order:
            item = self._items[item_id]
            if item.status == DownloadStatus.QUEUED:
                return item
        return None

    def notify_changed(self, item: DownloadItem) -> None:
        """Signal that an item already in the queue has been mutated in place."""
        self.item_changed.emit(item)
