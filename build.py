from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from app.core.version import APP_NAME, APP_VERSION

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
EXECUTABLE_NAME = "MediaDownloader"
SPEC_FILE = ROOT / f"{EXECUTABLE_NAME}.spec"
ENTRY_POINT = ROOT / "main.py"

# (source, destination) pairs, both relative to ROOT, bundled alongside the executable
# so ConfigManager and theme.load_stylesheet can find them at runtime via
# app.core.paths.get_project_root(), which resolves correctly whether frozen or not.
_DATA_DIRECTORIES: tuple[tuple[str, str], ...] = (
    ("app/config", "app/config"),
    ("resources", "resources"),
)


def clean() -> None:
    """Remove artifacts from previous builds."""
    for path in (DIST_DIR, BUILD_DIR, SPEC_FILE):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()


def _add_data_args() -> list[str]:
    separator = ";" if sys.platform == "win32" else ":"
    args: list[str] = []
    for source, destination in _DATA_DIRECTORIES:
        source_path = ROOT / source
        if not source_path.exists():
            continue
        args += ["--add-data", f"{source_path}{separator}{destination}"]
    return args


def _icon_args() -> list[str]:
    icon_extension = "ico" if sys.platform == "win32" else "icns" if sys.platform == "darwin" else "png"
    icon_path = ROOT / "assets" / "logo" / f"icon.{icon_extension}"
    return ["--icon", str(icon_path)] if icon_path.exists() else []


def build() -> int:
    """Invoke PyInstaller to produce a single-file executable with bundled resources."""
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        EXECUTABLE_NAME,
        *_add_data_args(),
        *_icon_args(),
        str(ENTRY_POINT),
    ]
    result = subprocess.run(command, cwd=ROOT)
    return result.returncode


def main() -> int:
    print(f"Building {APP_NAME} v{APP_VERSION} for {sys.platform}...")
    clean()
    exit_code = build()
    if exit_code == 0:
        print(f"Build succeeded. Executable located in: {DIST_DIR}")
    else:
        print("Build failed.", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
