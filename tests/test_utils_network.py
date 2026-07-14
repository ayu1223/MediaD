from __future__ import annotations

import urllib.error
from io import BytesIO

from app.utils import network as network_module
from app.utils.network import http_get


class _FakeResponse:
    def __init__(self, status: int, body: bytes, content_type: str) -> None:
        self.status = status
        self._body = BytesIO(body)
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_http_get_returns_response_on_success(monkeypatch):
    fake_response = _FakeResponse(200, b"hello", "text/plain")
    monkeypatch.setattr(network_module.urllib.request, "urlopen", lambda *_a, **_k: fake_response)

    result = http_get("https://example.com")

    assert result is not None
    assert result.status_code == 200
    assert result.content == b"hello"
    assert result.content_type == "text/plain"


def test_http_get_returns_none_on_url_error(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(network_module.urllib.request, "urlopen", _raise)

    assert http_get("https://example.com") is None


def test_http_get_returns_none_on_timeout(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr(network_module.urllib.request, "urlopen", _raise)

    assert http_get("https://example.com") is None
