from __future__ import annotations

from app.database.database import Database


class SettingsRepository:
    """Persists lightweight internal application state as key-value pairs.

    This is intentionally separate from app.core.config's JSON preferences file:
    core.config holds user-facing, hand-editable settings (theme, download directory, etc.),
    while this repository holds internal runtime state (e.g. last-used UI layout, cached
    lookups) that belongs in the database rather than a human-readable config file.
    """

    def __init__(self, database: Database) -> None:
        self._db = database

    def get(self, key: str, default: str | None = None) -> str | None:
        rows = self._db.query("SELECT value FROM app_state WHERE key = ?", (key,))
        return rows[0]["value"] if rows else default

    def set(self, key: str, value: str) -> None:
        self._db.execute(
            "INSERT INTO app_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def delete(self, key: str) -> None:
        self._db.execute("DELETE FROM app_state WHERE key = ?", (key,))

    def get_all(self) -> dict[str, str]:
        rows = self._db.query("SELECT key, value FROM app_state")
        return {row["key"]: row["value"] for row in rows}
