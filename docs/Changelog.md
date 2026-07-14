# Changelog

All notable changes to this project are documented here. Versioning is informal during
initial development (`0.x`); phases refer to the development plan this project was
built against.

## [Unreleased]

### Phase 12 — Packaging
- Fixed `build.py` to bundle `app/config/` and `resources/` as PyInstaller data
  directories; without this the packaged executable would crash on first launch
  (`ConfigManager` could not find its bundled default template).
- Added `--icon` support in `build.py` (auto-detected per platform from
  `assets/logo/`, no-ops if absent).
- Added `docs/Architecture.md`, `docs/Changelog.md`, `docs/Roadmap.md`.
- Rewrote `README.md` to reflect the completed application rather than the Phase-1
  scaffold.

### Phase 11 — Testing
- Added a 132-test suite (`tests/`) covering configuration, theming, the database
  layer, both repositories, the downloader engine/queue/scheduling logic, URL
  validation, progress throttling, metadata extraction, the direct-HTTP provider,
  filesystem/formatting/network utilities, and the settings/history/thumbnail/file
  services.
- Added `pytest.ini` and `requirements-dev.txt`.

### Phase 10 — Integration
- Added `app/ui/main_window.py` as the application's composition root, replacing the
  placeholder window `main.py` previously launched.
- Wired all five services (`DownloadService`, `HistoryService`, `SettingsService`,
  `ThumbnailService`, `UpdateService`) and both repositories into a working tabbed UI
  (Download, Playlist, Queue, History, Settings, About).
- Completed downloads are now recorded to history (`HistoryService.add()`, new).
- Wired `SignalBus` for cross-cutting status/error reporting to the status bar.
- Added a confirmation dialog for destructive history actions, gated by the existing
  `confirm_before_delete` setting.
- Added window geometry persistence via `SettingsRepository`.
- `HomePage` now emits `playlist_fetched` so a fetched playlist can be routed to the
  dedicated `PlaylistPage` for entry-by-entry selection, in addition to the existing
  whole-playlist download from `HomePage` itself.

### Phases 1-9 — Foundation through Pages
- Project scaffold, core utilities (config, logging, paths, theming, signal bus).
- Typed dataclass models for media info, playlists, download items, history items,
  and settings.
- SQLite database wrapper with migration support; history and settings repositories.
- Service layer: download, history, settings, file, thumbnail, and update services.
- `QThread`-based workers for fetching, downloading, and thumbnail retrieval.
- Downloader engine with a pluggable provider abstraction (`DirectHttpProvider`,
  `YtDlpProvider`), metadata extraction, queue management, and concurrency-aware
  download scheduling.
- Widget library (thumbnail, progress card, queue table, quality selector, folder
  selector, URL input, status bar) and page library (Home, Playlist, Downloads,
  History, Settings, About), each built against its service dependency but not yet
  assembled into a running application.
