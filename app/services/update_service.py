from __future__ import annotations

import json
import threading
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from app.core.constants import UPDATE_CHECK_URL
from app.core.logger import get_logger
from app.core.version import APP_VERSION
from app.utils.network import http_get

_logger = get_logger(__name__)


@dataclass(slots=True)
class UpdateInfo:
    update_available: bool
    latest_version: str | None = None
    download_url: str | None = None


class UpdateService(QObject):
    """Checks for application updates without blocking the calling thread."""

    check_finished = Signal(object)

    def check_for_updates_async(self) -> None:
        """Start a background update check; check_finished is emitted with an UpdateInfo when done."""
        thread = threading.Thread(target=self._run_check, daemon=True)
        thread.start()

    def _run_check(self) -> None:
        result = self._check_for_updates()
        self.check_finished.emit(result)

    def _check_for_updates(self) -> UpdateInfo:
        if not UPDATE_CHECK_URL:
            _logger.info("Update checking is disabled (no UPDATE_CHECK_URL configured).")
            return UpdateInfo(update_available=False)

        response = http_get(UPDATE_CHECK_URL)
        if response is None or response.status_code != 200:
            _logger.warning("Update check failed to reach %s", UPDATE_CHECK_URL)
            return UpdateInfo(update_available=False)

        try:
            payload = json.loads(response.content)
            latest_version = str(payload["version"])
            download_url = payload.get("url")
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            _logger.error("Malformed update feed response: %s", error)
            return UpdateInfo(update_available=False)

        is_newer = _is_newer_version(latest_version, APP_VERSION)
        return UpdateInfo(update_available=is_newer, latest_version=latest_version, download_url=download_url)


def _is_newer_version(candidate: str, current: str) -> bool:
    def parse(version: str) -> tuple[int, ...]:
        return tuple(int(part) for part in version.split(".") if part.isdigit())

    try:
        return parse(candidate) > parse(current)
    except ValueError:
        return False
