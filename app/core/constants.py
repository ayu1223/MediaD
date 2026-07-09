"""
Application-wide constants.
"""

from pathlib import Path

# ------------------------------
# Window
# ------------------------------

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850

MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 700

SIDEBAR_WIDTH = 230

APP_PADDING = 20

# ------------------------------
# Theme
# ------------------------------

DEFAULT_THEME = "Dark"

SUPPORTED_THEMES = (
    "Dark",
    "Light",
)

# ------------------------------
# Downloads
# ------------------------------

DEFAULT_DOWNLOAD_DIRECTORY = (
    Path.home()
    / "Downloads"
    / "MediaDownloader"
)

MAX_CONCURRENT_DOWNLOADS = 3

# ------------------------------
# Networking
# ------------------------------

REQUEST_TIMEOUT = 20

USER_AGENT = (
    "MediaDownloader/1.0"
)

# ------------------------------
# History
# ------------------------------

MAX_HISTORY_ITEMS = 1000