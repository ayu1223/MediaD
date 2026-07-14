"""Misc small widgets: badge, empty state, animated progress, spinner."""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QConicalGradient
from PySide6.QtWidgets import (
    QLabel, QProgressBar, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
)
import qtawesome as qta

from ..theme import PRIMARY, SECONDARY, ACCENT, TEXT_MUTED, TEXT, BORDER_SOFT


STATUS_STYLES = {
    "Ready":       ("#5EA2FF", "rgba(94,162,255,0.14)"),
    "Downloading": ("#7C5CFF", "rgba(124,92,255,0.16)"),
    "Completed":   ("#4ADE80", "rgba(74,222,128,0.14)"),
    "Paused":      ("#FBBF24", "rgba(251,191,36,0.14)"),
    "Failed":      ("#F87171", "rgba(248,113,113,0.14)"),
    "Queued":      ("#8B96A8", "rgba(139,150,168,0.14)"),
}


class StatusBadge(QLabel):
    def __init__(self, text: str = "Ready", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(text)
        self.setFixedHeight(24)
        self.setContentsMargins(10, 0, 10, 0)
        self._apply(text)

    def _apply(self, text: str):
        color, bg = STATUS_STYLES.get(text, STATUS_STYLES["Ready"])
        self.setStyleSheet(
            f"color: {color}; background: {bg};"
            f"border-radius: 12px; padding: 0 12px; font-size: 11px; font-weight: 600;"
        )
        self.setText(text)


class AnimatedProgressBar(QProgressBar):
    def __init__(self, value: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernProgress")
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self._anim = QPropertyAnimation(self, b"value", self)
        self._anim.setDuration(700)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setValue(0)
        QTimer.singleShot(80, lambda: self.animateTo(value))

    def animateTo(self, v: int):
        self._anim.stop()
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(v)
        self._anim.start()


class EmptyState(QWidget):
    def __init__(self, title: str, subtitle: str = "", icon_name: str = "fa6s.inbox", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 40, 0, 40)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ic = QLabel()
        ic.setPixmap(qta.icon(icon_name, color=TEXT_MUTED).pixmap(48, 48))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ic)

        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
        lay.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
            s.setWordWrap(True)
            s.setMaximumWidth(360)
            lay.addWidget(s, 0, Qt.AlignmentFlag.AlignHCenter)


class LoadingSpinner(QWidget):
    def __init__(self, size: int = 24, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._t = QTimer(self)
        self._t.timeout.connect(self._spin)
        self._t.start(24)

    def _spin(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        # backdrop ring
        pen = QPen(QColor(BORDER_SOFT), 3)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)
        # gradient arc
        grad = QConicalGradient(rect.center(), -self._angle)
        grad.setColorAt(0.0, QColor(PRIMARY))
        grad.setColorAt(0.5, QColor(SECONDARY))
        grad.setColorAt(1.0, QColor(ACCENT))
        pen = QPen(grad, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, self._angle * 16, 120 * 16)
        p.end()


class Toast(QFrame):
    """A single self-dismissing notification pill (Task 5).

    Lightweight, consistent with the rest of this module's hand-rolled widgets
    (StatusBadge, EmptyState, etc.) rather than pulling in a third-party toast
    library — the app has no existing notification framework to integrate with,
    so this is the "lightweight solution consistent with the existing
    architecture" the task calls for.
    """

    _KIND_STYLES = {
        "info": ("#5EA2FF", "rgba(94,162,255,0.16)", "fa6s.circle-info"),
        "success": ("#4ADE80", "rgba(74,222,128,0.16)", "fa6s.circle-check"),
        "error": ("#F87171", "rgba(248,113,113,0.16)", "fa6s.circle-exclamation"),
    }

    def __init__(self, text: str, kind: str = "info", parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        color, bg, icon_name = self._KIND_STYLES.get(kind, self._KIND_STYLES["info"])

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 16, 10)
        lay.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(16, 16))
        lay.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600;")
        text_lbl.setWordWrap(True)
        lay.addWidget(text_lbl, 1)

        self.setStyleSheet(
            f"#Toast {{ background: {bg}; border: 1px solid {color}; border-radius: 10px; }}"
        )
        self.setMaximumWidth(360)

        self._opacity_effect = None
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_in.setDuration(180)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.start()

    def fade_out(self, on_finished) -> None:
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(on_finished)
        anim.start()
        self._fade_out_anim = anim  # keep a reference alive until it finishes


class ToastHost(QWidget):
    """Stacks active Toasts bottom-right of whatever it's placed over.

    Call notify(text, kind) to show a new toast; it auto-dismisses after a
    few seconds. Multiple toasts stack vertically, newest at the bottom.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(8)
        self._lay.addStretch()
        self._toasts: list[Toast] = []

    def notify(self, text: str, kind: str = "info", duration_ms: int = 4000) -> None:
        toast = Toast(text, kind, parent=self)
        self._lay.insertWidget(self._lay.count() - 1, toast)
        self._toasts.append(toast)
        toast.show()
        QTimer.singleShot(duration_ms, lambda: self._dismiss(toast))

    def _dismiss(self, toast: Toast) -> None:
        if toast not in self._toasts:
            return

        def _remove():
            self._toasts.remove(toast)
            self._lay.removeWidget(toast)
            toast.deleteLater()

        toast.fade_out(_remove)


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Separator")
        self.setFixedHeight(1)
