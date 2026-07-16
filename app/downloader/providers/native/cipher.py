"""Signature deciphering — deliberately out of scope, by design.

YouTube's web player obfuscates some adaptive-format stream URLs by running them
through a signature-transformation function embedded in a minified, versioned
JavaScript player file (base.js). Solving that generally requires: downloading
the current player file, locating and parsing the obfuscated transform function
(name changes with every YouTube player release), and replaying its operations
(reverse/splice/swap) against the signature. yt-dlp maintains this at real,
ongoing cost — it changes often enough that a hand-rolled copy here would go
stale quickly and silently produce broken downloads, which is worse than not
having it.

Instead (see constants.py's client-context comment), this extractor sticks to
InnerTube client contexts (ANDROID, IOS) that are served formats with a direct,
already-usable "url" field and no cipher step at all. This module's only job is
to detect the rare case where even those clients hand back a cipher-gated
format, so the caller can raise CipherRequiredError and let the composite
YouTubeProvider transparently fall back to yt-dlp — which *does* implement full
cipher support — rather than attempting a half-working decrypt here.

If a future contributor wants to implement real deciphering, this is the module
to extend: give decipher_signature() a real implementation and have formats.py
call it instead of raising when requires_cipher() is True.
"""
from __future__ import annotations


def requires_cipher(format_entry: dict) -> bool:
    """Return True if this InnerTube format needs signature deciphering to be
    playable, i.e. it has no direct "url" field and instead carries a
    "signatureCipher" or "cipher" field that would need to be decoded."""
    return "url" not in format_entry and ("signatureCipher" in format_entry or "cipher" in format_entry)


def decipher_signature(cipher_field: str) -> str:
    """Not implemented — see module docstring for why. Always raises."""
    raise NotImplementedError(
        "Native signature deciphering is not implemented; formats requiring it are "
        "filtered out upstream so the caller can fall back to yt-dlp instead."
    )