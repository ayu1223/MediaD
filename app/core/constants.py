from __future__ import annotations

CONFIG_FILE_NAME = "settings.json"
CONFIG_TEMPLATE_RELATIVE_PATH = "config/settings.json"
DATABASE_FILE_NAME = "media_downloader.db"

LOG_FILE_NAME = "media_downloader.log"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5

DEFAULT_WINDOW_WIDTH = 1180
DEFAULT_WINDOW_HEIGHT = 720

SUPPORTED_VIDEO_QUALITIES: tuple[str, ...] = ("2160p", "1440p", "1080p", "720p", "480p", "360p")
SUPPORTED_AUDIO_FORMATS: tuple[str, ...] = ("mp3", "m4a", "opus", "flac", "wav")

DEFAULT_MAX_CONCURRENT_DOWNLOADS = 3

THUMBNAIL_CACHE_DIRNAME = "thumbnails"

# Left empty until a real release feed exists; update_service treats an empty
# value as "update checking disabled" rather than failing.
UPDATE_CHECK_URL = ""

