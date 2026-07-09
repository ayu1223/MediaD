"""
Shared Qt signals.
"""

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):

    metadata_fetched = Signal(object)

    metadata_failed = Signal(str)

    download_started = Signal(object)

    download_progress = Signal(object)

    download_finished = Signal(object)

    download_failed = Signal(str)


signals = AppSignals()