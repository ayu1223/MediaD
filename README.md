# Media Downloader

A modern desktop application built with Python and PySide6 for downloading and
managing supported online media.

The application is layered so additional media providers can be added without major
architectural changes, and is not tightly coupled to any single provider.

## Status

All twelve development phases are complete: the application launches to a working
tabbed UI (Download, Playlist, Queue, History, Settings, About), backed by a real
SQLite-persisted history and JSON-persisted settings, a unit test suite, and a
packaging script that produces a standalone executable. See `docs/Changelog.md` for
phase-by-phase detail and `docs/Roadmap.md` for known limitations and future work.

## Architecture

```
UI -> Services -> Downloader / Database -> Workers (QThread)
```

- The UI never talks to Workers, the Downloader, or the Database directly — only
  through Services.
- Workers run on `QThread` and communicate via Qt signals; the UI thread never blocks.
- Media provider logic is isolated behind a provider abstraction so new providers can
  be added without touching the UI.

See `docs/Architecture.md` for the full breakdown, and `app/` for the package layout:
`core`, `ui`, `downloader`, `workers`, `database`, `models`, `services`, `utils`.

## Requirements

- Python 3.12+
- `ffmpeg` on `PATH` (optional but recommended — enables merging separate audio/video
  streams and embedding thumbnails; downloads still work without it where the source
  provides a single combined stream)
- See `requirements.txt`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Building a standalone executable

```bash
pip install -r requirements.txt   # includes pyinstaller
python build.py
```

Produces a standalone, windowed executable in `dist/`. The build bundles the default
configuration template and `resources/` alongside the executable so the packaged app
runs without needing the source tree present.

To add an application icon, place `assets/logo/icon.ico` (Windows), `icon.icns`
(macOS), or `icon.png` (Linux) before building — `build.py` picks it up automatically.

## Configuration and data locations

User-facing settings, the history database, logs, and cached thumbnails are stored
outside the project directory in the OS-appropriate application data folder (see
`app/core/paths.py`):

| OS | Location |
|---|---|
| Windows | `%APPDATA%\MediaDownloader\` |
| macOS | `~/Library/Application Support/MediaDownloader/` |
| Linux | `$XDG_DATA_HOME/MediaDownloader/` (falls back to `~/.local/share/MediaDownloader/`) |

## License

MIT — see `LICENSE`.
