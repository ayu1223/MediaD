from __future__ import annotations

from app.utils.file_utils import delete_file, ensure_directory, free_space_bytes, sanitize_filename, unique_path


def test_sanitize_filename_strips_invalid_characters():
    assert sanitize_filename('a<b>c:d"e/f\\g|h?i*j') == "a_b_c_d_e_f_g_h_i_j"


def test_sanitize_filename_empty_becomes_untitled():
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("...") == "untitled"


def test_sanitize_filename_truncates_long_names():
    long_name = "a" * 500
    assert len(sanitize_filename(long_name)) == 200


def test_unique_path_returns_original_when_no_collision(tmp_path):
    candidate = tmp_path / "file.txt"
    assert unique_path(candidate) == candidate


def test_unique_path_appends_counter_on_collision(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "file (1).txt").write_text("x")

    result = unique_path(tmp_path / "file.txt")

    assert result == tmp_path / "file (2).txt"


def test_ensure_directory_creates_nested_path(tmp_path):
    target = tmp_path / "a" / "b" / "c"

    result = ensure_directory(target)

    assert result == target
    assert target.is_dir()


def test_free_space_bytes_returns_positive_value(tmp_path):
    assert free_space_bytes(tmp_path) > 0


def test_delete_file_removes_existing_file(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")

    assert delete_file(target) is True
    assert not target.exists()


def test_delete_file_missing_file_returns_false(tmp_path):
    assert delete_file(tmp_path / "missing.txt") is False


def test_delete_file_does_not_remove_directories(tmp_path):
    directory = tmp_path / "dir"
    directory.mkdir()

    assert delete_file(directory) is False
    assert directory.exists()
