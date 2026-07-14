from __future__ import annotations

import pytest

from app.core.config import ConfigManager
from app.services import settings_service as settings_service_module
from app.services.settings_service import SettingsService


@pytest.fixture
def config_manager(tmp_path):
    template_path = tmp_path / "template.json"
    template_path.write_text(
        '{"version": 1, "download_directory": "", "max_concurrent_downloads": 3, '
        '"default_video_quality": "1080p", "default_audio_format": "mp3", "theme": "dark", '
        '"window_geometry": null, "confirm_before_delete": true, "check_for_updates": true}',
        encoding="utf-8",
    )
    return ConfigManager(config_path=tmp_path / "settings.json", template_path=template_path)


@pytest.fixture(autouse=True)
def stub_default_download_dir(monkeypatch, tmp_path):
    fallback_dir = tmp_path / "Downloads"
    monkeypatch.setattr(settings_service_module, "get_default_download_dir", lambda: fallback_dir)
    return fallback_dir


def test_load_fills_in_default_download_directory_when_blank(config_manager, stub_default_download_dir):
    service = SettingsService(config_manager)

    assert service.get_settings().download_directory == str(stub_default_download_dir)


def test_load_preserves_configured_download_directory(config_manager):
    config_manager.save({**config_manager.load_default(), "download_directory": "/custom/path"})

    service = SettingsService(config_manager)

    assert service.get_settings().download_directory == "/custom/path"


def test_save_settings_persists_and_emits_signal(config_manager):
    service = SettingsService(config_manager)
    received = []
    service.settings_changed.connect(received.append)

    updated = service.get_settings()
    updated.theme = "light"
    service.save_settings(updated)

    assert received[0].theme == "light"
    assert config_manager.load()["theme"] == "light"


def test_update_applies_partial_changes(config_manager):
    service = SettingsService(config_manager)

    result = service.update(max_concurrent_downloads=8)

    assert result.max_concurrent_downloads == 8
    assert result.theme == "dark"  # unrelated fields untouched
    assert service.get_settings().max_concurrent_downloads == 8
