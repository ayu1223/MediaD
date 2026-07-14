from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass

from app.core.logger import get_logger

_logger = get_logger(__name__)
_DEFAULT_TIMEOUT_SECONDS = 10
_USER_AGENT = "MediaDownloader/0.1.0"


@dataclass(slots=True)
class HttpResponse:
    status_code: int
    content: bytes
    content_type: str | None


def http_get(url: str, timeout: float = _DEFAULT_TIMEOUT_SECONDS) -> HttpResponse | None:
    """Perform a simple HTTP GET. Returns None on any network error rather than raising."""
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return HttpResponse(
                status_code=response.status,
                content=response.read(),
                content_type=response.headers.get("Content-Type"),
            )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as error:
        _logger.warning("HTTP GET failed for %s: %s", url, error)
        return None
