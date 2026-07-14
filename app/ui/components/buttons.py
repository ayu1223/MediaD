"""Modern buttons with hover animations."""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QPushButton
import qtawesome as qta

from ..theme import PRIMARY, SECONDARY, DANGER, TEXT_MUTED
from .helpers import add_shadow


class _HoverLiftMixin:
    """Adds subtle lift on hover using shadow animation."""
    def _install_lift(self, base_blur=24, base_y=8, hover_blur=36, hover_y=14, color=PRIMARY):
        self._shadow = add_shadow(self, blur=base_blur, y=base_y, color=color, alpha=90)
        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._base_blur = base_blur
        self._hover_blur = hover_blur

    def enterEvent(self, e):
        if hasattr(self, "_anim"):
            self._anim.stop()
            self._anim.setStartValue(self._shadow.blurRadius())
            self._anim.setEndValue(self._hover_blur)
            self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if hasattr(self, "_anim"):
            self._anim.stop()
            self._anim.setStartValue(self._shadow.blurRadius())
            self._anim.setEndValue(self._base_blur)
            self._anim.start()
        super().leaveEvent(e)


class PrimaryButton(_HoverLiftMixin, QPushButton):
    def __init__(self, text: str = "", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(44)
        if icon_name:
            self.setIcon(qta.icon(icon_name, color="white"))
        self._install_lift(base_blur=24, base_y=10, hover_blur=42, color=PRIMARY)


class SecondaryButton(QPushButton):
    def __init__(self, text: str = "", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SecondaryBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(42)
        if icon_name:
            self.setIcon(qta.icon(icon_name, color="#E6EDF3"))


class DangerButton(QPushButton):
    def __init__(self, text: str = "", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("DangerBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(38)
        if icon_name:
            self.setIcon(qta.icon(icon_name, color=DANGER))


class GhostButton(QPushButton):
    def __init__(self, text: str = "", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("GhostBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(36)
        if icon_name:
            self.setIcon(qta.icon(icon_name, color=TEXT_MUTED))


class ChipButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("ChipBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(28)


class IconButton(QPushButton):
    def __init__(self, icon_name: str, tooltip: str = "", size: int = 38, parent=None):
        super().__init__(parent)
        self.setObjectName("IconBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(size, size)
        self.setIcon(qta.icon(icon_name, color="#E6EDF3"))
        if tooltip:
            self.setToolTip(tooltip)
