from __future__ import annotations

from dataclasses import dataclass

from .cipher import requires_cipher


@dataclass(slots=True, frozen=True)
class StreamFormat:
    """A single playable adaptive or progressive stream, as returned by InnerTube."""

    itag: int
    url: str
    mime_type: str
    is_video: bool
    is_audio: bool
    height: int | None
    abr_kbps: int | None  # audio bitrate, kbps — only meaningful when is_audio
    filesize_bytes: int | None
    is_progressive: bool  # True if this single stream carries both video and audio

    @property
    def container(self) -> str:
        """File extension implied by mime_type, e.g. "mp4", "webm"."""
        return self.mime_type.split("/")[-1].split(";")[0] if "/" in self.mime_type else "bin"


def parse_formats(player_response: dict) -> list[StreamFormat]:
    """Parse every usable (non-cipher-gated) format out of a player response's
    streamingData. Cipher-gated formats are silently skipped here — see
    cipher.py — since this extractor only ever uses client contexts that
    predominantly avoid them; if *every* format ends up cipher-gated, the
    resulting empty list is what triggers CipherRequiredError upstream in
    youtube_client.py.
    """
    streaming_data = player_response.get("streamingData", {}) or {}
    raw_formats = list(streaming_data.get("formats") or []) + list(streaming_data.get("adaptiveFormats") or [])

    formats: list[StreamFormat] = []
    for raw in raw_formats:
        if requires_cipher(raw):
            continue
        url = raw.get("url")
        mime_type = raw.get("mimeType", "")
        if not url or not mime_type:
            continue

        is_audio = mime_type.startswith("audio/")
        is_video = mime_type.startswith("video/")
        is_progressive = is_video and "audioQuality" in raw  # progressive video formats also carry audio

        formats.append(
            StreamFormat(
                itag=raw.get("itag", 0),
                url=url,
                mime_type=mime_type,
                is_video=is_video,
                is_audio=is_audio,
                height=raw.get("height"),
                abr_kbps=(raw.get("averageBitrate") or raw.get("bitrate") or 0) // 1000 if is_audio else None,
                filesize_bytes=raw.get("contentLength") and int(raw["contentLength"]),
                is_progressive=is_progressive,
            )
        )
    return formats


def available_video_qualities(formats: list[StreamFormat]) -> list[str]:
    """Distinct video heights present, formatted like "1080p", descending."""
    heights = sorted({f.height for f in formats if f.is_video and f.height}, reverse=True)
    return [f"{height}p" for height in heights]


def select_video_format(formats: list[StreamFormat], requested_quality: str) -> StreamFormat:
    """Pick the video-only (preferred, for muxing with the best separate audio)
    or progressive format closest to requested_quality (Issue 2: graceful
    fallback to the nearest available resolution rather than failing outright
    when the exact one isn't present for this video).
    """
    video_formats = [f for f in formats if f.is_video and f.height]
    if not video_formats:
        raise ValueError("No video formats available.")

    requested_height = _parse_height(requested_quality)
    if requested_height is None:
        # "best"/unrecognized -> highest available.
        return max(video_formats, key=lambda f: f.height or 0)

    # Prefer the closest height <= requested (avoid downloading more than asked
    # for); if nothing is that small, fall back to the smallest available above
    # it — either way, always returns *some* usable format rather than raising.
    not_larger = [f for f in video_formats if (f.height or 0) <= requested_height]
    if not_larger:
        return max(not_larger, key=lambda f: f.height or 0)
    return min(video_formats, key=lambda f: f.height or 0)


def select_audio_format(formats: list[StreamFormat]) -> StreamFormat:
    """Pick the highest-bitrate audio-only format available."""
    audio_formats = [f for f in formats if f.is_audio]
    if not audio_formats:
        raise ValueError("No audio formats available.")
    return max(audio_formats, key=lambda f: f.abr_kbps or 0)


def _parse_height(quality: str) -> int | None:
    digits = "".join(char for char in quality if char.isdigit())
    return int(digits) if digits else None