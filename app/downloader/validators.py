from __future__ import annotations

from urllib.parse import urlparse


class InvalidURLError(ValueError):
    """Raised when a URL fails validation before being passed to a provider."""


def is_valid_url(url: str) -> bool:
    """Return True if url is a well-formed http(s) URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_or_raise(url: str) -> str:
    """Return the trimmed URL if valid, otherwise raise InvalidURLError."""
    trimmed = (url or "").strip()
    if not is_valid_url(trimmed):
        raise InvalidURLError(f"'{url}' is not a valid http(s) URL.")
    return trimmed
