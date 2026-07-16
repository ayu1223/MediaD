"""Constants for talking to YouTube's InnerTube API directly.

InnerTube is the internal API the youtube.com and mobile-app frontends themselves
call — it isn't a secret or an exploit, and yt-dlp's own YouTube extractor is
itself built on top of it. What *is* deliberately narrow here is the choice of
client context: YouTube's ANDROID and IOS clients are served formats with a
direct "url" field already present (no "signatureCipher"/"cipher" field to
decrypt), because those clients' own apps don't run a JS signature-descrambling
routine the way the youtube.com web player does. Sticking to those clients is
what lets this extractor avoid implementing full signature deciphering (see
cipher.py) while still working for the large majority of videos.
"""
from __future__ import annotations

INNERTUBE_HOST = "https://www.youtube.com"
INNERTUBE_PLAYER_URL = f"{INNERTUBE_HOST}/youtubei/v1/player"
INNERTUBE_BROWSE_URL = f"{INNERTUBE_HOST}/youtubei/v1/browse"
INNERTUBE_NEXT_URL = f"{INNERTUBE_HOST}/youtubei/v1/next"

# Public, well-known API key used by YouTube's own web client to call InnerTube;
# present in every youtube.com page's source and used identically by yt-dlp.
INNERTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"

# Ordered client contexts to try for player requests. ANDROID first (simplest,
# most reliable direct-URL formats), then IOS as a second attempt if ANDROID's
# response is empty/restricted for a given video.
CLIENT_CONTEXTS: dict[str, dict] = {
    "ANDROID": {
        "clientName": "ANDROID",
        "clientVersion": "19.09.37",
        "androidSdkVersion": 30,
        "userAgent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
        "hl": "en",
        "gl": "US",
    },
    "IOS": {
        "clientName": "IOS",
        "clientVersion": "19.09.3",
        "deviceModel": "iPhone14,3",
        "userAgent": "com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)",
        "hl": "en",
        "gl": "US",
    },
}
PLAYER_CLIENT_ORDER = ("ANDROID", "IOS")

# Playlist/browse metadata doesn't involve stream URLs at all, so the WEB client
# (broadest, most complete metadata) is fine there — no cipher concern applies.
WEB_CLIENT_CONTEXT = {
    "clientName": "WEB",
    "clientVersion": "2.20240101.00.00",
    "hl": "en",
    "gl": "US",
}

REQUEST_TIMEOUT_SECONDS = 15