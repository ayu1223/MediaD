from __future__ import annotations

import sys

from app.core import paths as paths_module
from app.core.paths import get_ffmpeg_location


def test_prefers_bundled_ffmpeg_when_present(monkeypatch, tmp_path):
    monkeypatch.setattr(paths_module, "get_project_root", lambda: tmp_path)
    ffmpeg_dir = tmp_path / "resources" / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True)
    binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    (ffmpeg_dir / binary_name).write_text("stub")
    monkeypatch.setattr(paths_module.shutil, "which", lambda name: "/should/not/be/used/ffmpeg")

    assert get_ffmpeg_location() == ffmpeg_dir


def test_falls_back_to_path_when_not_bundled(monkeypatch, tmp_path):
    monkeypatch.setattr(paths_module, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(paths_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    assert get_ffmpeg_location() == paths_module.Path("/usr/bin")


def test_returns_none_when_neither_bundled_nor_on_path(monkeypatch, tmp_path):
    monkeypatch.setattr(paths_module, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(paths_module.shutil, "which", lambda name: None)

    assert get_ffmpeg_location() is None
