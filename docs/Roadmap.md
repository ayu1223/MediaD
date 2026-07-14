# Roadmap

## Known limitations at v0.1.0

- **No `.qss` stylesheets are shipped.** `resources/themes/` is bundled but empty;
  `theme.py` falls back to default Qt styling gracefully, but neither "dark" nor
  "light" currently looks different from the platform default.
- **No application icon is shipped.** `build.py` will pick one up automatically from
  `assets/logo/icon.{ico,icns,png}` if added.
- **`UpdateService` has no real feed configured.** `UPDATE_CHECK_URL` in
  `app/core/constants.py` is intentionally blank, which disables the check rather than
  failing; point it at a real release-manifest URL to enable it.
- **Playlist thumbnails are not fetched.** `PlaylistPage` lists entries as plain text;
  `ThumbnailService`/`ThumbnailWorker` are only wired into `HomePage` today.
- **No retry logic.** A failed download or metadata fetch must be re-initiated
  manually by the user; there is no automatic backoff/retry.
- **Single-window, single-profile.** There is no multi-window support and no concept
  of user profiles or accounts.

## Candidate future work

- Author actual dark/light `.qss` stylesheets.
- Add thumbnail loading to `PlaylistPage` entries.
- Add a "reveal in file manager" / "open file" action to completed queue and history
  entries (`FileService.reveal_in_file_manager` already exists and is unused by the UI).
- Add automatic retry with exponential backoff for transient download failures.
- Add a real update feed and wire `UpdateService.check_finished` to an in-app "download
  update" action rather than just a status message.
- Expand provider coverage beyond `DirectHttpProvider`/`YtDlpProvider` — the provider
  abstraction (`app/downloader/providers/base.py`) was designed for this; a new
  provider is a subclass plus one `DownloaderEngine.register()` call.
- Add a widget-level UI test pass (`QTest`) alongside the existing business-logic
  test suite in `tests/`.
- Add CI (lint + `pytest`) once the project has a hosted repository.
