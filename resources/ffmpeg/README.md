# Bundled ffmpeg

This directory is empty by default. `app.core.paths.get_ffmpeg_location()` checks here
first, then falls back to `ffmpeg` on `PATH`. If `ffmpeg` is already on `PATH` on your
machine, you don't need to do anything — merging/audio-embedding will work as-is.

To bundle ffmpeg into a packaged build (so end users don't need it on `PATH`), download
a static build for each target platform and place the binaries directly in this folder:

- **Windows**: `resources/ffmpeg/ffmpeg.exe` (and `ffprobe.exe`)
  — https://www.gyan.dev/ffmpeg/builds/ (the "essentials" build is sufficient)
- **macOS**: `resources/ffmpeg/ffmpeg` (and `ffprobe`)
  — https://evermeet.cx/ffmpeg/
- **Linux**: `resources/ffmpeg/ffmpeg` (and `ffprobe`)
  — https://johnvansickle.com/ffmpeg/

On macOS/Linux, make sure the binary is executable: `chmod +x resources/ffmpeg/ffmpeg`.

`build.py` already bundles this entire directory into the packaged executable via
`--add-data`, so once the binaries are placed here, no further packaging changes are
needed.
