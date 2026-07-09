"""
Application paths.
"""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

APP_DIR = ROOT_DIR / "app"

RESOURCES_DIR = ROOT_DIR / "resources"

ICONS_DIR = RESOURCES_DIR / "icons"

IMAGES_DIR = RESOURCES_DIR / "images"

FONTS_DIR = RESOURCES_DIR / "fonts"

THEMES_DIR = RESOURCES_DIR / "themes"

LOGS_DIR = ROOT_DIR / "logs"

DOWNLOADS_DIR = ROOT_DIR / "downloads"

DOCS_DIR = ROOT_DIR / "docs"

TESTS_DIR = ROOT_DIR / "tests"

ASSETS_DIR = ROOT_DIR / "assets"

CONFIG_DIR = APP_DIR / "config"

DATABASE_DIR = ROOT_DIR / "database"


def create_directories() -> None:
    """
    Create runtime directories if they don't exist.
    """

    directories = (
        LOGS_DIR,
        DOWNLOADS_DIR,
    )

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


create_directories()