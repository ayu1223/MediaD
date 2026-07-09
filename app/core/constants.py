"""
Global application constants.
"""

from pathlib import Path

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850

SUPPORTED_THEMES = [
    "Dark",
    "Light",
]

DEFAULT_THEME = "Dark"

DEFAULT_DOWNLOAD_FOLDER = Path.home() / "Downloads" / "MediaDownloader"

SUPPORTED_VIDEO_EXTENSIONS = [
    ".mp4",
    ".mkv",
    ".webm",
]

SUPPORTED_AUDIO_EXTENSIONS = [
    ".mp3",
    ".m4a",
    ".wav",
]

MAX_CONCURRENT_DOWNLOADS = 3