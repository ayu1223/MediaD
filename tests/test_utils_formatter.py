from __future__ import annotations

import pytest

from app.utils.formatter import format_bytes, format_duration, format_eta, format_speed


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (512, "512 B"),
        (1024, "1.0 KB"),
        (1024 * 1024, "1.0 MB"),
        (1536 * 1024, "1.5 MB"),
        (1024 * 1024 * 1024, "1.0 GB"),
        (1024**4, "1.0 TB"),
        (1024**5, "1024.0 TB"),
    ],
)
def test_format_bytes(size, expected):
    assert format_bytes(size) == expected


def test_format_bytes_negative_clamped_to_zero():
    assert format_bytes(-100) == "0 B"


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (None, ""),
        (5, "0:05"),
        (65, "1:05"),
        (3661, "1:01:01"),
    ],
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


def test_format_speed_appends_per_second():
    assert format_speed(1024) == "1.0 KB/s"


def test_format_eta_unknown_returns_empty():
    assert format_eta(None) == ""
    assert format_eta(-1) == ""


def test_format_eta_known_value():
    assert format_eta(65) == "1:05 remaining"
