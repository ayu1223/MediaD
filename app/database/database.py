from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.logger import get_logger
from app.core.paths import get_database_path

_logger = get_logger(__name__)

_SCHEMA_VERSION = 1

_MIGRATIONS: dict[int, str] = {
    1: """
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            provider TEXT NOT NULL,
            source_url TEXT NOT NULL,
            file_path TEXT NOT NULL,
            media_type TEXT NOT NULL,
            quality TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            completed_at TEXT NOT NULL,
            thumbnail_url TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_history_completed_at ON history (completed_at);

        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """,
}


class Database:
    """Owns the SQLite connection, schema migrations, and thread-safe query execution."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or get_database_path()
        self._lock = threading.Lock()
        self._connection = self._connect()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def _migrate(self) -> None:
        with self._lock:
            current_version = self._connection.execute("PRAGMA user_version;").fetchone()[0]
            if current_version >= _SCHEMA_VERSION:
                return
            for version in range(current_version + 1, _SCHEMA_VERSION + 1):
                script = _MIGRATIONS.get(version)
                if script is None:
                    _logger.error("Missing migration script for schema version %d", version)
                    raise RuntimeError(f"Missing migration script for schema version {version}")
                _logger.info("Applying database migration to version %d", version)
                self._connection.executescript(script)
                self._connection.execute(f"PRAGMA user_version = {version};")
            self._connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Execute a block of statements atomically, committing on success and rolling back on error."""
        with self._lock:
            cursor = self._connection.cursor()
            try:
                yield cursor
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                _logger.exception("Database transaction failed; rolled back.")
                raise
            finally:
                cursor.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single statement and commit immediately."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            return cursor

    def query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a read-only query and return all matching rows."""
        with self._lock:
            cursor = self._connection.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def close(self) -> None:
        with self._lock:
            self._connection.close()
