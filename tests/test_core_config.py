from __future__ import annotations

import json

import pytest

from app.core.config import ConfigManager


@pytest.fixture
def template_path(tmp_path):
    path = tmp_path / "template.json"
    path.write_text(json.dumps({"theme": "dark", "max_concurrent_downloads": 3}), encoding="utf-8")
    return path


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "settings.json"


def test_load_creates_from_template_when_missing(config_path, template_path):
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    data = manager.load()

    assert data == {"theme": "dark", "max_concurrent_downloads": 3}
    assert config_path.exists()


def test_load_returns_existing_valid_config(config_path, template_path):
    config_path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    data = manager.load()

    assert data == {"theme": "light"}


def test_load_recovers_from_corrupted_json(config_path, template_path):
    config_path.write_text("{not valid json", encoding="utf-8")
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    data = manager.load()

    assert data == {"theme": "dark", "max_concurrent_downloads": 3}
    corrupted_backups = list(config_path.parent.glob("settings.corrupted-*.json"))
    assert len(corrupted_backups) == 1


def test_load_recovers_from_non_dict_root(config_path, template_path):
    config_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    data = manager.load()

    assert data == {"theme": "dark", "max_concurrent_downloads": 3}


def test_save_writes_atomically(config_path, template_path):
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    manager.save({"theme": "light", "max_concurrent_downloads": 5})

    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "theme": "light",
        "max_concurrent_downloads": 5,
    }
    assert not config_path.with_suffix(".tmp").exists()


def test_load_default_reads_template_directly(config_path, template_path):
    manager = ConfigManager(config_path=config_path, template_path=template_path)

    assert manager.load_default() == {"theme": "dark", "max_concurrent_downloads": 3}
