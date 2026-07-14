from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.database.database import Database
from app.models.history_item import HistoryItem, MediaType


class HistoryRepository:
    """Persists and retrieves completed download records."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def add(self, item: HistoryItem) -> None:
        self._db.execute(
            """
            INSERT OR REPLACE INTO history
                (id, title, provider, source_url, file_path, media_type, quality,
                 file_size_bytes, completed_at, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.title,
                item.provider,
                item.source_url,
                str(item.file_path),
                item.media_type.value,
                item.quality,
                item.file_size_bytes,
                item.completed_at.isoformat(),
                item.thumbnail_url,
            ),
        )

    def get_all(self) -> list[HistoryItem]:
        rows = self._db.query("SELECT * FROM history ORDER BY completed_at DESC")
        return [self._row_to_item(row) for row in rows]

    def get_by_id(self, item_id: str) -> HistoryItem | None:
        rows = self._db.query("SELECT * FROM history WHERE id = ?", (item_id,))
        return self._row_to_item(rows[0]) if rows else None

    def search(self, query_text: str) -> list[HistoryItem]:
        rows = self._db.query(
            "SELECT * FROM history WHERE title LIKE ? ORDER BY completed_at DESC",
            (f"%{query_text}%",),
        )
        return [self._row_to_item(row) for row in rows]

    def delete(self, item_id: str) -> None:
        self._db.execute("DELETE FROM history WHERE id = ?", (item_id,))

    def clear(self) -> None:
        self._db.execute("DELETE FROM history")

    @staticmethod
    def _row_to_item(row) -> HistoryItem:
        return HistoryItem(
            id=row["id"],
            title=row["title"],
            provider=row["provider"],
            source_url=row["source_url"],
            file_path=Path(row["file_path"]),
            media_type=MediaType(row["media_type"]),
            quality=row["quality"],
            file_size_bytes=row["file_size_bytes"],
            completed_at=datetime.fromisoformat(row["completed_at"]),
            thumbnail_url=row["thumbnail_url"],
        )
