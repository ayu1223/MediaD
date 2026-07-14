from __future__ import annotations

import pytest

from app.downloader.validators import InvalidURLError, is_valid_url, validate_or_raise


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/video",
        "http://example.com",
        "https://example.com/path?query=1",
    ],
)
def test_is_valid_url_accepts_http_https(url):
    assert is_valid_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        None,
        "not a url",
        "ftp://example.com/file",
        "example.com/no-scheme",
        "https://",
    ],
)
def test_is_valid_url_rejects_invalid(url):
    assert is_valid_url(url) is False


def test_validate_or_raise_trims_whitespace():
    assert validate_or_raise("  https://example.com  ") == "https://example.com"


def test_validate_or_raise_raises_on_invalid():
    with pytest.raises(InvalidURLError):
        validate_or_raise("not a url")
