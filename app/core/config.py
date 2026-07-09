"""
Configuration manager.
"""

import json
from pathlib import Path

from app.core.constants import (
    DEFAULT_DOWNLOAD_DIRECTORY,
    DEFAULT_THEME,
)

CONFIG_PATH = Path("app/config/settings.json")


DEFAULT_CONFIG = {
    "theme": DEFAULT_THEME,
    "download_directory": str(DEFAULT_DOWNLOAD_DIRECTORY),
}


class Config:

    @staticmethod
    def load() -> dict:

        if not CONFIG_PATH.exists():

            Config.save(DEFAULT_CONFIG)

            return DEFAULT_CONFIG

        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def save(config: dict) -> None:

        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                indent=4,
            )