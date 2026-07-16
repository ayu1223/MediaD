from __future__ import annotations

import json
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


def http_post_json(
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
    timeout: float = _DEFAULT_TIMEOUT_SECONDS,
) -> dict | None:
    """POST a JSON payload and parse a JSON response. Returns None on any network,
    HTTP, or JSON-decoding error rather than raising — callers that need to
    distinguish failure reasons should catch at a higher level (this is used by
    the native YouTube extractor, which treats any None here as "fall back to
    yt-dlp" rather than a hard error).
    """
    body = json.dumps(payload).encode("utf-8")
    request_headers = {"User-Agent": _USER_AGENT, "Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as error:
        _logger.warning("HTTP POST failed for %s: %s", url, error)
        return None
    except json.JSONDecodeError as error:
        _logger.warning("HTTP POST to %s returned invalid JSON: %s", url, error)
        return None