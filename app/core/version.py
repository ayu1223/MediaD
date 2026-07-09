"""
Application version information.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    """Application version information."""

    app_name: str
    version: str
    author: str
    description: str


APP = Version(
    app_name="Media Downloader",
    version="1.0.0",
    author="Ayush Lokare",
    description="Modern desktop media downloader built with Python and PySide6.",
)