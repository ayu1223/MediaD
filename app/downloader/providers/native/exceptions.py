
from __future__ import annotations


class NativeExtractionError(Exception):
    """Raised whenever the native YouTube extractor cannot satisfy a request.

    This is the single signal YouTubeProvider (see ../youtube_native_provider.py)
    watches for to transparently fall back to YtDlpProvider — every failure mode
    inside the native/ package (network errors, an unparseable player response, a
    format that needs signature deciphering we deliberately don't implement, a
    playlist we can't resolve, etc.) should raise this rather than a bare/generic
    exception, so the fallback is a deliberate, understood contract rather than
    "catch everything and hope".
    """


class CipherRequiredError(NativeExtractionError):
    """Raised when every candidate stream for a video requires signature
    deciphering to resolve a playable URL.

    The native extractor deliberately does not implement YouTube's signature
    cipher (see cipher.py for why) — this exception is how that scope boundary
    surfaces as a normal, expected fallback rather than a crash.
    """