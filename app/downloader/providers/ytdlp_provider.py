# app/downloader/providers/ytdlp_provider.py
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from urllib.parse import urlparse

from app.core.constants import SUPPORTED_AUDIO_FORMATS
from app.core.logger import get_logger
from app.core.paths import get_ffmpeg_location
from app.downloader.progress import build_progress_hook
from app.downloader.providers.base import ProgressCallback, Provider
from app.models.download_item import DownloadItem
from app.models.media_info import MediaInfo
from app.models.playlist import PlaylistInfo

_logger = get_logger(__name__)

_PROGRESS_TEMPLATE = "%(progress)j"
_AUTO_DETECT_JS_RUNTIME = "auto"
_AUTO_DETECT_COOKIES = "auto"
_JS_RUNTIME_CANDIDATES = ("node", "deno", "bun")
_DEFAULT_REMOTE_COMPONENTS = "ejs:github"
# Stream-copy both tracks into an mkv container instead of forcing mp4. YouTube's
# best audio is typically Opus, which mp4 cannot hold, so forcing mp4 previously
# meant yt-dlp silently re-encoded Opus -> a low/default-bitrate AAC on every merge
# (audible as crackle/distortion). mkv holds Opus natively, so both tracks get a
# true, lossless stream copy.
_MERGE_OUTPUT_FORMAT = "mkv"
_MERGE_AUDIO_CODEC_ARGS = "Merger+ffmpeg_o1:-c:v copy -c:a copy"

# --- Issue 1/4/7: HTTP 403s and outdated yt-dlp configuration ---------------
# A bare yt-dlp invocation with no explicit User-Agent/retry/timeout configuration
# is the single biggest cause of intermittent 403s: YouTube's edge servers are far
# more likely to serve a 403 to a request that looks like a bare script than one
# that presents a normal browser's headers, and a single failed attempt with no
# retry surfaces as a hard failure to the user even when a second attempt (yt-dlp's
# own retry machinery, or ours) would have succeeded.
_MODERN_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_DEFAULT_HTTP_HEADERS = (
    ("User-Agent", _MODERN_USER_AGENT),
    ("Accept-Language", "en-US,en;q=0.9"),
)
_YTDLP_RETRIES = "10"
_YTDLP_FRAGMENT_RETRIES = "10"
_YTDLP_RETRY_SLEEP = "exp=1:30"  # exponential backoff between yt-dlp's own retries, capped at 30s
_YTDLP_SOCKET_TIMEOUT = "30"

# Application-level retry: yt-dlp's own --retries covers retrying within a single
# invocation (a dropped connection mid-fragment, for example), but a 403 on the
# *initial* player-response request can still surface as a single hard failure.
# Retrying the whole subprocess a few times, with backoff, recovers from the
# transient cases without masking a genuinely broken URL (which will keep failing
# identically and still surface an error after the final attempt).
_APP_LEVEL_RETRY_ATTEMPTS = 3
_APP_LEVEL_RETRY_BACKOFF_SECONDS = (2, 5)  # sleep before attempt 2, then attempt 3

# --- Issue 2: cookie fallback chain -----------------------------------------
# Order matters and matches the requested fallback: Chrome -> Edge -> Firefox ->
# user-provided cookies.txt -> no cookies at all. Each candidate is only actually
# *attempted* (by running the real yt-dlp command) when cookies_from_browser is
# left at its default "auto"; an explicitly-configured value is tried first, with
# cookies_file (if any) and finally "none" as fallbacks — see _cookie_candidates.
_BROWSER_COOKIE_CANDIDATES = ("chrome", "edge", "firefox")
_BOT_CHECK_MARKERS = ("sign in to confirm", "not a bot", "confirm you're not a bot")
_FORBIDDEN_MARKERS = ("403", "forbidden")

# --- Bot-check fallback without cookies -------------------------------------
# When every cookie source has been exhausted (or none are available/working —
# e.g. Chrome/Edge locked because the browser is running, Firefox profile not
# found) and YouTube still returns a "sign in to confirm you're not a bot"
# response, forcing yt-dlp's youtube extractor to impersonate the Android or
# iOS client (instead of the default web client) frequently avoids the
# bot-check entirely, since those clients use a different, non-PO-token-gated
# player API. This costs nothing when cookies already worked (it's only tried
# as a last resort) and needs no user setup (no cookies.txt, no closing the
# browser), so it turns a previously-fatal, environment-dependent failure into
# one the app can usually recover from on its own.
_PLAYER_CLIENT_FALLBACKS = ("android", "ios")
_TRANSIENT_NETWORK_MARKERS = (
    "timed out", "timeout", "connection reset", "connection refused",
    "temporary failure", "502", "503", "504", "bad gateway", "service unavailable",
)
# Substrings yt-dlp/browser-cookie3 emit when it *cannot access* a browser's cookie
# store at all (locked database, browser currently running, missing profile,
# decryption failure, etc.) — see https://github.com/yt-dlp/yt-dlp/issues/7271.
# These are access failures, not "cookies are required" failures, and should move
# on to the next candidate rather than aborting. Includes the exact per-browser
# phrasing yt-dlp uses ("could not copy <browser> cookie database", "could not
# find <browser> cookies database") as well as generic fallback substrings.
_COOKIE_ACCESS_MARKERS = (
    "could not copy chrome cookie database",
    "could not copy edge cookie database",
    "could not copy firefox cookie database",
    "could not find chrome cookies database",
    "could not find edge cookies database",
    "could not find firefox cookies database",
    "could not copy",
    "could not find",
    "could not decrypt",
    "could not locate",
    "failed to decrypt",
    "failed to load cookies",
    "unable to load cookies",
    "cookie database",
    "cookies database",
    "browser cookies",
    "database is locked",
    "permission denied",
    "unsupported browser",
    "no such file or directory",
)


class YtDlpError(Exception):
    """Raised when the yt-dlp CLI subprocess fails or returns unparseable output."""


class YtDlpProvider(Provider):
    """Provider backed by the yt-dlp CLI (invoked via `python -m yt_dlp`), acting as the
    generic fallback for hosting-page URLs (YouTube, Vimeo, Twitter/X, Instagram,
    Facebook, Reddit, TikTok, and anything else yt-dlp's extractors cover).

    Uses subprocess rather than the yt_dlp Python API so that CLI-only features
    (JS runtimes, remote components, browser cookies, impersonation) are available and
    so the provider stays compatible with yt-dlp releases that change their internal
    Python API without changing their CLI contract.
    """

    name = "yt-dlp"

    def __init__(
        self,
        js_runtime: str | None = _AUTO_DETECT_JS_RUNTIME,
        remote_components: str | None = _DEFAULT_REMOTE_COMPONENTS,
        cookies_file: str | None = None,
        cookies_from_browser: str | None = _AUTO_DETECT_COOKIES,
        impersonate: str | None = None,
        write_subtitles: bool = False,
        write_auto_subtitles: bool = False,
        subtitle_languages: str = "en",
        embed_chapters: bool = False,
        sponsorblock_categories: str | None = None,
        extra_args: list[str] | None = None,
    ) -> None:
        """js_runtime defaults to "auto": if a JS runtime (node/deno/bun) is found on
        PATH it is used automatically so YouTube's JS-challenge/signature checks are
        handled without any per-user configuration; pass None explicitly to disable it,
        or a specific runtime name to force one. remote_components defaults to
        "ejs:github" since it is harmless to specify even without a JS runtime present.

        cookies_from_browser defaults to "auto" (Issue 2): at fetch/download time, the
        provider tries Chrome, then Edge, then Firefox, then a configured cookies_file,
        then finally no cookies at all — moving to the next candidate on any cookie
        *access* failure (locked database, browser currently running, unreadable
        profile, browser not installed, etc. — see
        https://github.com/yt-dlp/yt-dlp/issues/7271) rather than aborting. A warning
        is logged for each skipped candidate. An authentication error is only raised
        if yt-dlp explicitly indicates cookies are required (a "sign in to confirm
        you're not a bot"-style response) after the chain is exhausted — a failure to
        access one browser's cookie database is never treated as fatal on its own.

        Pass None explicitly to disable browser-cookie usage entirely, or a specific
        browser name ("chrome"/"edge"/"firefox"/etc., anything yt-dlp's
        --cookies-from-browser accepts) to force one as the first candidate — either
        way, cookies_file (if also given) and finally "none" are still tried as
        fallbacks; see _cookie_candidates.

        cookies_file, if given, is used as a Netscape-format cookies.txt. When
        cookies_from_browser is "auto" (the default), it is tried after all three
        browsers as the last resort before giving up on cookies entirely.
        """
        self._js_runtime = self._resolve_js_runtime(js_runtime)
        self._remote_components = remote_components
        self._cookies_file = cookies_file
        self._cookies_from_browser = cookies_from_browser
        self._impersonate = impersonate
        self._write_subtitles = write_subtitles
        self._write_auto_subtitles = write_auto_subtitles
        self._subtitle_languages = subtitle_languages
        self._embed_chapters = embed_chapters
        self._sponsorblock_categories = sponsorblock_categories
        self._extra_args = extra_args or []

    @staticmethod
    def _resolve_js_runtime(js_runtime: str | None) -> str | None:
        if js_runtime != _AUTO_DETECT_JS_RUNTIME:
            return js_runtime
        for candidate in _JS_RUNTIME_CANDIDATES:
            if shutil.which(candidate):
                return candidate
        _logger.info("No JS runtime (node/deno/bun) found on PATH; proceeding without --js-runtimes.")
        return None

    def set_cookies_file(self, cookies_file: str | None) -> None:
        """Update the configured cookies.txt path at runtime (Settings page).

        A user-supplied cookies.txt from an already-logged-in browser session is
        the most reliable fix for YouTube's bot-check: unlike
        --cookies-from-browser it doesn't need the browser open (so it isn't
        blocked by a locked cookie database) and doesn't depend on player-client
        fallback tricks working. See _cookie_candidates for where it sits in the
        fallback order (tried after all three browsers, before giving up)."""
        self._cookies_file = cookies_file or None

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    # ------------------------------------------------------------------
    # Cookie fallback chain (Issue 2)
    # ------------------------------------------------------------------

    def _cookie_candidates(self) -> list[tuple[str, list[str]]]:
        """Return an ordered list of (label, extra_cli_args) candidates to try.

        The last candidate is always ("none", []) so the chain always terminates in
        "proceed without cookies" rather than raising for lack of a working source.
        """
        if self._cookies_from_browser == _AUTO_DETECT_COOKIES:
            candidates = [(browser, ["--cookies-from-browser", browser]) for browser in _BROWSER_COOKIE_CANDIDATES]
            if self._cookies_file:
                candidates.append(("cookies.txt", ["--cookies", self._cookies_file]))
            candidates.append(("none", []))
            return candidates

        if self._cookies_from_browser:
            candidates = [(self._cookies_from_browser, ["--cookies-from-browser", self._cookies_from_browser])]
            if self._cookies_file:
                candidates.append(("cookies.txt", ["--cookies", self._cookies_file]))
            candidates.append(("none", []))
            return candidates

        if self._cookies_file:
            return [("cookies.txt", ["--cookies", self._cookies_file]), ("none", [])]

        return [("none", [])]

    def _should_try_next_cookie(self, stderr: str) -> bool:
        """True only for a cookie-*access* failure (locked/missing browser cookie
        store, undecryptable database, browser not installed, etc.) — never for an
        unrelated yt-dlp error. Used by _run_with_cookie_fallback to decide whether
        to move on to the next cookie candidate instead of failing outright."""
        stderr_lower = stderr.lower()
        return any(marker in stderr_lower for marker in _COOKIE_ACCESS_MARKERS)

    def _run_with_cookie_fallback(
        self,
        command_builder: Callable[[list[str]], list[str]],
        executor: Callable[[list[str]], subprocess.CompletedProcess],
    ) -> subprocess.CompletedProcess:
        """Single source of truth for cookie fallback + transient-failure retry,
        used by both extract() and download().

        For each cookie candidate in order (see _cookie_candidates):
          - success -> return immediately.
          - cookie-access failure (_should_try_next_cookie) -> move to the next
            candidate immediately, no backoff (locked/missing browser database).
          - bot-check response -> move to the next candidate too (a different
            cookie source, or none, may not be flagged); only fatal once the
            *last* candidate ("none") also hits it.
          - HTTP 403 / transient network error -> retry the *same* candidate a
            few times with backoff (yt-dlp's own --retries covers mid-download
            drops within one attempt; this covers a 403 on the initial request).
          - anything else (invalid URL, private/removed video, 404, unsupported
            URL, etc.) -> raise immediately, no further cycling through cookie
            candidates.

        Because _cookie_candidates() always ends in ("none", []), a chain that
        fails purely due to cookie-access problems naturally ends with one
        attempt made with no cookies at all before raising.

        executor actually runs a built command and returns a
        CompletedProcess-like result (.returncode/.stdout/.stderr). extract()
        passes a thin subprocess.run wrapper; download() passes a wrapper around
        its streaming Popen call, so the exact same fallback/retry decision
        logic governs both instead of two separate, divergent implementations.
        """
        candidates = self._cookie_candidates()
        last_result: subprocess.CompletedProcess | None = None

        for candidate_index, (label, cookie_args) in enumerate(candidates):
            is_last_candidate = candidate_index == len(candidates) - 1
            command = command_builder(cookie_args)

            for attempt in range(1, _APP_LEVEL_RETRY_ATTEMPTS + 1):
                result = executor(command)

                if result.returncode == 0:
                    if candidate_index > 0:
                        _logger.info("Succeeded using cookie source '%s'.", label)
                    elif attempt > 1:
                        _logger.info("Succeeded on retry attempt %d.", attempt)
                    return result

                last_result = result
                stderr = result.stderr or ""

                if self._should_try_next_cookie(stderr) and not is_last_candidate:
                    _logger.warning(
                        "Cookie source '%s' unavailable (%s); trying next.", label, stderr.strip()[-200:]
                    )
                    break  # next candidate, no backoff — this isn't a transient issue

                stderr_lower = stderr.lower()
                is_bot_check = any(marker in stderr_lower for marker in _BOT_CHECK_MARKERS)
                if is_bot_check:
                    if is_last_candidate:
                        _logger.warning(
                            "Bot-check response with no cookie sources left; "
                            "trying player-client fallbacks."
                        )
                        fallback_result = self._try_player_client_fallbacks(command_builder, executor)
                        if fallback_result is not None:
                            return fallback_result
                        raise YtDlpError(
                            "YouTube still requested bot verification after trying every cookie "
                            "source and player-client fallback; no working source was available. "
                            "Try closing Chrome/Edge (their cookie databases are locked while "
                            "running) or exporting a cookies.txt file."
                        )
                    _logger.warning("Bot-check response using cookie source '%s'; trying next.", label)
                    break

                is_forbidden = any(marker in stderr_lower for marker in _FORBIDDEN_MARKERS)
                is_transient = any(marker in stderr_lower for marker in _TRANSIENT_NETWORK_MARKERS)
                if attempt < _APP_LEVEL_RETRY_ATTEMPTS and (is_forbidden or is_transient):
                    backoff = _APP_LEVEL_RETRY_BACKOFF_SECONDS[
                        min(attempt - 1, len(_APP_LEVEL_RETRY_BACKOFF_SECONDS) - 1)
                    ]
                    _logger.warning(
                        "yt-dlp failed (attempt %d/%d, %s); retrying in %ds.",
                        attempt, _APP_LEVEL_RETRY_ATTEMPTS,
                        "HTTP 403" if is_forbidden else "transient network error", backoff,
                    )
                    time.sleep(backoff)
                    continue

                # Not a cookie problem, not a bot-check, not (further) retryable: a
                # real failure (invalid URL, private/removed video, 404, unsupported
                # URL, etc.). Raise now rather than cycling remaining cookie
                # candidates, which would only delay a failure that won't change.
                raise YtDlpError(self._format_error("yt-dlp failed", result))

        assert last_result is not None
        raise YtDlpError(self._format_error("yt-dlp failed", last_result))

    def _try_player_client_fallbacks(
        self,
        command_builder: Callable[[list[str]], list[str]],
        executor: Callable[[list[str]], subprocess.CompletedProcess],
    ) -> subprocess.CompletedProcess | None:
        """Last-resort bot-check bypass: retry with no cookies, forcing yt-dlp's
        youtube extractor to use the Android then iOS client player API instead
        of the default web client (see _PLAYER_CLIENT_FALLBACKS). Returns the
        successful result, or None if every fallback also failed."""
        for client in _PLAYER_CLIENT_FALLBACKS:
            extra_args = ["--extractor-args", f"youtube:player_client={client}"]
            command = command_builder(extra_args)
            result = executor(command)
            if result.returncode == 0:
                _logger.info("Succeeded using player-client fallback '%s'.", client)
                return result
            _logger.warning(
                "Player-client fallback '%s' also failed (%s).",
                client, (result.stderr or "").strip()[-200:],
            )
        return None

    def extract(self, url: str) -> MediaInfo | PlaylistInfo:
        def build_command(cookie_args: list[str]) -> list[str]:
            return [
                *self._base_command(),
                "--dump-single-json",
                "--no-warnings",
                "--skip-download",
                *cookie_args,
                *self._non_cookie_auth_args(),
                *self._runtime_args(),
                *self._header_args(),
                *self._resilience_args(),
                url,
            ]

        def run(command: list[str]) -> subprocess.CompletedProcess:
            return subprocess.run(command, capture_output=True, text=True)

        result = self._run_with_cookie_fallback(build_command, run)

        try:
            info = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise YtDlpError(f"yt-dlp returned invalid JSON for {url}: {error}") from error

        if info.get("_type") == "playlist":
            entries = [self._to_media_info(entry) for entry in (info.get("entries") or []) if entry]
            _logger.info("Extracted playlist '%s' (%d entries) for %s", info.get("title"), len(entries), url)
            return PlaylistInfo(
                id=str(info.get("id", url)),
                title=info.get("title") or "Untitled Playlist",
                provider=self.name,
                source_url=url,
                thumbnail_url=info.get("thumbnail"),
                entries=entries,
            )
        _logger.info("Extracted metadata for '%s' (%s)", info.get("title"), url)
        return self._to_media_info(info)

    def download(self, item: DownloadItem, progress_cb: ProgressCallback, cancel_event: threading.Event) -> None:
        hook = build_progress_hook(progress_cb, cancel_event)
        item.destination_path.parent.mkdir(parents=True, exist_ok=True)

        def build_command(cookie_args: list[str]) -> list[str]:
            return [
                *self._base_command(),
                "--no-warnings",
                "--no-playlist",
                "--newline",
                "--progress-template",
                _PROGRESS_TEMPLATE,
                "-f",
                self._build_format_selector(item),
                "-o",
                str(item.destination_path),
                *cookie_args,
                *self._non_cookie_auth_args(),
                *self._runtime_args(),
                *self._header_args(),
                *self._resilience_args(),
                *self._postprocessing_args(item),
                item.media_info.source_url,
            ]

        def run(command: list[str]) -> subprocess.CompletedProcess:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
            )
            try:
                self._stream_progress(process, hook)
            except Exception:
                process.kill()
                process.wait()
                self._cleanup_partial_files(item)
                if cancel_event.is_set():
                    _logger.info("Download cancelled: '%s' (%s)", item.media_info.title, item.id)
                raise  # cancellation (or any streaming error) stops immediately —
                       # never treated as "try the next cookie source"

            stderr_output = process.stderr.read() if process.stderr is not None else ""
            return_code = process.wait()
            if return_code != 0:
                self._cleanup_partial_files(item)
            return subprocess.CompletedProcess(command, return_code, stdout="", stderr=stderr_output)

        _logger.info("Download started: '%s' (%s, quality=%s)", item.media_info.title, item.id, item.quality)
        self._run_with_cookie_fallback(build_command, run)
        _logger.info("Download completed: '%s' (%s)", item.media_info.title, item.id)

    @staticmethod
    def _cleanup_partial_files(item: DownloadItem) -> None:
        """Issue 5: remove any partial output left behind by a failed or cancelled
        download. yt-dlp writes to *.part (and *.ytdl for resume metadata) while
        downloading, and may also leave a fully-written-but-not-yet-merged file at
        the final destination path if it fails during the merge/postprocessing step.
        None of these should be left around masquerading as a real download."""
        destination = item.destination_path
        candidates = [destination, destination.with_suffix(destination.suffix + ".part")]
        candidates += list(destination.parent.glob(f"{destination.stem}*.part"))
        candidates += list(destination.parent.glob(f"{destination.stem}*.ytdl"))

        for path in {p for p in candidates if p.exists()}:
            try:
                path.unlink()
                _logger.info("Cleaned up partial file after failed/cancelled download: %s", path)
            except OSError as error:
                _logger.warning("Could not remove partial file %s: %s", path, error)

    def _stream_progress(self, process: subprocess.Popen, hook: Callable[[dict], None]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                status = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(status, dict):
                hook(status)

    def _base_command(self) -> list[str]:
        command = [sys.executable, "-m", "yt_dlp"]
        ffmpeg_dir = get_ffmpeg_location()
        if ffmpeg_dir is not None:
            command += ["--ffmpeg-location", str(ffmpeg_dir)]
        return command + self._extra_args

    def _non_cookie_auth_args(self) -> list[str]:
        args: list[str] = []
        if self._impersonate:
            args += ["--impersonate", self._impersonate]
        return args

    def _runtime_args(self) -> list[str]:
        args: list[str] = []
        if self._js_runtime:
            args += ["--js-runtimes", self._js_runtime]
        if self._remote_components:
            args += ["--remote-components", self._remote_components]
        return args

    def _header_args(self) -> list[str]:
        """Issue 1/7: a modern User-Agent and Accept-Language header make requests
        look like an ordinary browser rather than a bare script, which measurably
        reduces spurious 403s from YouTube's edge servers."""
        args: list[str] = []
        for name, value in _DEFAULT_HTTP_HEADERS:
            args += ["--add-header", f"{name}:{value}"]
        return args

    def _resilience_args(self) -> list[str]:
        """Issue 4: retry, backoff, and timeout handling using yt-dlp's own
        machinery (fragment retries, exponential retry-sleep, socket timeout),
        which covers transient failures within a single invocation. See
        _run_with_cookie_fallback for the complementary whole-invocation retry
        and cookie fallback chain."""
        return [
            "--retries", _YTDLP_RETRIES,
            "--fragment-retries", _YTDLP_FRAGMENT_RETRIES,
            "--retry-sleep", _YTDLP_RETRY_SLEEP,
            "--socket-timeout", _YTDLP_SOCKET_TIMEOUT,
        ]

    def _postprocessing_args(self, item: DownloadItem) -> list[str]:
        args: list[str] = []
        if item.audio_only:
            args += ["--extract-audio", "--audio-format", item.audio_format or "mp3"]
        else:
            args += ["--merge-output-format", _MERGE_OUTPUT_FORMAT, "--postprocessor-args", _MERGE_AUDIO_CODEC_ARGS]
        if self._write_subtitles:
            args += ["--write-subs", "--sub-langs", self._subtitle_languages]
        if self._write_auto_subtitles:
            args += ["--write-auto-subs", "--sub-langs", self._subtitle_languages]
        if self._embed_chapters:
            args += ["--embed-chapters"]
        if self._sponsorblock_categories:
            args += ["--sponsorblock-remove", self._sponsorblock_categories]
        return args

    def _to_media_info(self, info: dict) -> MediaInfo:
        formats = info.get("formats") or []
        heights = sorted(
            {f.get("height") for f in formats if f.get("vcodec") not in (None, "none") and f.get("height")},
            reverse=True,
        )
        return MediaInfo(
            id=str(info.get("id", "")),
            title=info.get("title") or "Untitled",
            provider=self.name,
            source_url=info.get("webpage_url") or info.get("original_url", ""),
            thumbnail_url=info.get("thumbnail"),
            duration_seconds=info.get("duration"),
            uploader=info.get("uploader"),
            available_qualities=[f"{h}p" for h in heights],
            available_audio_formats=list(SUPPORTED_AUDIO_FORMATS),
        )

    @staticmethod
    def _build_format_selector(item: DownloadItem) -> str:
        if item.audio_only:
            return "bestaudio/best"
        digits = "".join(char for char in item.quality if char.isdigit())
        if digits:
            return f"bestvideo*[height<={digits}]+bestaudio/best[height<={digits}]"
        return "bestvideo*+bestaudio/best"

    @staticmethod
    def _format_error(context: str, result: subprocess.CompletedProcess) -> str:
        detail = (result.stderr or result.stdout or "").strip()[-500:]
        return f"{context}: yt-dlp exited with code {result.returncode}: {detail}"