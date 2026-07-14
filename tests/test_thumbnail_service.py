from __future__ import annotations

from app.services import thumbnail_service as thumbnail_service_module
from app.services.thumbnail_service import ThumbnailService
from app.utils.network import HttpResponse


def test_get_cached_path_none_when_not_fetched(tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)

    assert service.get_cached_path("https://example.com/thumb.jpg") is None


def test_fetch_downloads_and_caches_image(monkeypatch, tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)
    response = HttpResponse(status_code=200, content=b"fake-image-bytes", content_type="image/png")
    monkeypatch.setattr(thumbnail_service_module, "http_get", lambda url: response)

    path = service.fetch("https://example.com/thumb.png")

    assert path is not None
    assert path.exists()
    assert path.suffix == ".png"
    assert path.read_bytes() == b"fake-image-bytes"


def test_fetch_reuses_cache_on_second_call(monkeypatch, tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)
    calls = []

    def fake_http_get(url):
        calls.append(url)
        return HttpResponse(status_code=200, content=b"data", content_type="image/jpeg")

    monkeypatch.setattr(thumbnail_service_module, "http_get", fake_http_get)

    first = service.fetch("https://example.com/thumb.jpg")
    second = service.fetch("https://example.com/thumb.jpg")

    assert first == second
    assert len(calls) == 1


def test_fetch_returns_none_on_failed_response(monkeypatch, tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)
    monkeypatch.setattr(thumbnail_service_module, "http_get", lambda url: None)

    assert service.fetch("https://example.com/thumb.jpg") is None


def test_fetch_returns_none_on_non_200_status(monkeypatch, tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)
    response = HttpResponse(status_code=404, content=b"", content_type=None)
    monkeypatch.setattr(thumbnail_service_module, "http_get", lambda url: response)

    assert service.fetch("https://example.com/missing.jpg") is None


def test_fetch_defaults_to_jpg_for_unknown_content_type(monkeypatch, tmp_path):
    service = ThumbnailService(cache_dir=tmp_path)
    response = HttpResponse(status_code=200, content=b"data", content_type="application/octet-stream")
    monkeypatch.setattr(thumbnail_service_module, "http_get", lambda url: response)

    path = service.fetch("https://example.com/thumb")

    assert path is not None
    assert path.suffix == ".jpg"
