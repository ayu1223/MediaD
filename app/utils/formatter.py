from __future__ import annotations

_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")


def format_bytes(size_bytes: float) -> str:
    """Format a byte count as a human-readable string, e.g. '12.3 MB'."""
    if size_bytes < 0:
        return "0 B"
    size = float(size_bytes)
    for unit in _SIZE_UNITS:
        if size < 1024 or unit == _SIZE_UNITS[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} {_SIZE_UNITS[-1]}"


def format_duration(seconds: int | None) -> str:
    """Format a duration in seconds as H:MM:SS or M:SS. Returns '' if None."""
    if seconds is None:
        return ""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_speed(bytes_per_sec: float) -> str:
    """Format a transfer rate, e.g. '1.2 MB/s'."""
    return f"{format_bytes(bytes_per_sec)}/s"


def format_eta(seconds: int | None) -> str:
    """Format an estimated time remaining, e.g. '2:15 remaining'. Returns '' if unknown."""
    if seconds is None or seconds < 0:
        return ""
    return f"{format_duration(seconds)} remaining"
