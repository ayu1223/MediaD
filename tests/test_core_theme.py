from __future__ import annotations

from app.core import theme as theme_module
from app.core.theme import Theme, load_stylesheet, theme_from_value


def test_theme_from_value_known():
    assert theme_from_value("light") is Theme.LIGHT
    assert theme_from_value("dark") is Theme.DARK


def test_theme_from_value_unknown_defaults_to_dark():
    assert theme_from_value("neon") is Theme.DARK


def test_load_stylesheet_missing_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(theme_module, "get_project_root", lambda: tmp_path)

    assert load_stylesheet(Theme.DARK) == ""


def test_load_stylesheet_reads_existing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(theme_module, "get_project_root", lambda: tmp_path)
    (tmp_path / "resources" / "themes").mkdir(parents=True)
    (tmp_path / "resources" / "themes" / "dark.qss").write_text("QWidget { color: white; }", encoding="utf-8")

    assert load_stylesheet(Theme.DARK) == "QWidget { color: white; }"
