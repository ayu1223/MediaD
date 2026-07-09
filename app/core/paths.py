"""
Centralized application paths.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

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