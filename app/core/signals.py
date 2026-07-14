from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """Application-wide signal hub for cross-cutting events not owned by a single worker or service."""

    status_message = Signal(str)
    error_occurred = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()


_signal_bus: SignalBus | None = None


def get_signal_bus() -> SignalBus:
    """Return the process-wide SignalBus instance, creating it on first use."""
    global _signal_bus
    if _signal_bus is None:
        _signal_bus = SignalBus()
    return _signal_bus
