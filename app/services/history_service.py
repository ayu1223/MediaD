from __future__ import annotations

from app.database.history_repository import HistoryRepository
from app.models.history_item import HistoryItem


class HistoryService:
    """The sole boundary the UI uses to read and manage download history.

    Wraps HistoryRepository so the UI never queries the database layer directly,
    per the mandated UI -> Services -> Database architecture (mirrors the same
    gap-fix rationale as DownloadService for the downloader layer).
    """

    def __init__(self, repository: HistoryRepository) -> None:
        self._repository = repository

    def add(self, item: HistoryItem) -> None:
        self._repository.add(item)

    def list_all(self) -> list[HistoryItem]:
        return self._repository.get_all()

    def search(self, query: str) -> list[HistoryItem]:
        if not query.strip():
            return self.list_all()
        return self._repository.search(query.strip())

    def delete(self, item_id: str) -> None:
        self._repository.delete(item_id)

    def clear(self) -> None:
        self._repository.clear()
