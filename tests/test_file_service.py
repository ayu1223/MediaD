from __future__ import annotations

from app.services.file_service import FileService


def test_build_destination_path_creates_directory_and_sanitizes_name(tmp_path):
    service = FileService()
    target_dir = tmp_path / "downloads"

    result = service.build_destination_path(target_dir, "My: Video?", "mp4")

    assert target_dir.is_dir()
    assert result == target_dir / "My_ Video_.mp4"


def test_build_destination_path_avoids_collision(tmp_path):
    service = FileService()
    target_dir = tmp_path / "downloads"
    target_dir.mkdir()
    (target_dir / "video.mp4").write_text("existing")

    result = service.build_destination_path(target_dir, "video", "mp4")

    assert result == target_dir / "video (1).mp4"


def test_has_sufficient_space_true_for_small_requirement(tmp_path):
    service = FileService()

    assert service.has_sufficient_space(tmp_path, required_bytes=1) is True


def test_has_sufficient_space_false_for_impossible_requirement(tmp_path):
    service = FileService()

    assert service.has_sufficient_space(tmp_path, required_bytes=10**18) is False


def test_delete_returns_true_when_file_removed(tmp_path):
    service = FileService()
    target = tmp_path / "file.mp4"
    target.write_text("data")

    assert service.delete(target) is True
    assert not target.exists()


def test_delete_returns_false_when_file_missing(tmp_path):
    service = FileService()

    assert service.delete(tmp_path / "missing.mp4") is False
