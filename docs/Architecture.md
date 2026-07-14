# Architecture

## Layering

Media Downloader follows a strict one-directional dependency chain:

```
UI  ->  Services  ->  Downloader / Database  ->  Workers (QThread)
```

- **UI** (`app/ui/`) never imports `app/downloader/` or `app/workers/` directly. Every
  page and widget talks only to a `*Service` class.
- **Services** (`app/services/`) are the sole boundary the UI is allowed to cross. They
  own no business logic themselves beyond coordination — `DownloadService` wraps
  `DownloadManager`/`QueueManager`/`MetadataExtractor`; `HistoryService` wraps
  `HistoryRepository`; `SettingsService` wraps `ConfigManager`.
- **Downloader** (`app/downloader/`) contains all provider and download-orchestration
  logic and knows nothing about Qt widgets or the database.
- **Database** (`app/database/`) contains the SQLite connection and two repositories.
  Nothing outside `app/services/` and `app/ui/main_window.py` (the composition root)
  touches it directly.
- **Workers** (`app/workers/`) are thin `QThread` subclasses that run a single callable
  off the UI thread and report back via signals. They contain no business logic.

`app/core/` (config, logging, paths, theming, the app-wide `SignalBus`) and
`app/models/` (typed dataclasses) are used by every layer and depend on nothing above
them.

## Composition root

`app/ui/main_window.py` is the only place that constructs `Database`, the two
repositories, and all five services. Pages receive already-constructed services through
their constructors; no page or widget instantiates a service or repository itself. This
keeps every other module unit-testable in isolation (see `tests/`).

## Provider abstraction

New media sources are added by subclassing `app.downloader.providers.base.Provider` and
registering an instance with `DownloaderEngine` — no other layer needs to change.
`DownloaderEngine.find_provider()` returns the first registered provider whose
`can_handle()` returns `True`; `DirectHttpProvider` (URLs pointing straight at a media
file) is checked before the generic `YtDlpProvider` fallback.

## Threading model

The UI thread must never block. Every operation that touches the network, disk I/O of
non-trivial size, or `yt-dlp`/`ffmpeg` subprocesses runs on a `QThread`:

| Worker | Runs | Reports via |
|---|---|---|
| `FetchWorker` | `MetadataExtractor.extract()` | `finished_ok(MediaInfo\|PlaylistInfo)`, `failed(str)` |
| `DownloadWorker` | a `Provider.download()` callable | `progress(item)`, `finished_ok(item)`, `failed(item, str)` |
| `ThumbnailWorker` | `ThumbnailService.fetch()` | `finished_ok(url, path)` |

`DownloadManager` owns scheduling: it holds a `max_concurrent` limit, starts a new
`DownloadWorker` whenever a slot frees up, and relays each worker's signals outward as
its own `progress`/`item_completed`/`item_failed`/`queue_changed` signals. Cancellation
is cooperative — `DownloadWorker.cancel()` sets a `threading.Event` that provider
`download()` implementations must check periodically.

## Cross-cutting events

`app.core.signals.SignalBus` is a process-wide, no-argument-construction `QObject`
carrying two signals — `status_message` and `error_occurred` — for events that don't
belong to one specific worker or service. `MainWindow` is the sole subscriber today,
relaying bus events to the status bar; any future component (a tray icon, a
notification center) could subscribe independently without new plumbing.

## Persistence

Two independent stores exist, deliberately kept separate:

- **`app/core/config.py` (`ConfigManager`)** — a human-editable JSON file
  (`settings.json`) holding user-facing preferences (theme, download directory,
  concurrency limit). Recovers automatically from corruption by quarantining the bad
  file and reseeding from the bundled template.
- **`app/database/database.py` (`Database`, SQLite)** — holds the `history` table
  (completed downloads) and an `app_state` key-value table used for internal,
  non-user-facing state such as window geometry. Migrations are numbered and applied
  incrementally via `PRAGMA user_version`.

## Packaging

`build.py` invokes PyInstaller in `--onefile --windowed` mode and bundles
`app/config/` and `resources/` as data directories so `ConfigManager` and
`theme.load_stylesheet()` can find them at runtime — both frozen and unfrozen, since
`app.core.paths.get_project_root()` resolves relative to `__file__`, which PyInstaller
rewrites to the extraction directory automatically.
