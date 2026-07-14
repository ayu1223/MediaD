"""Small helpers for shadows, icons and gradient thumbnails."""
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import (
    QColor, QPixmap, QPainter, QLinearGradient, QBrush, QFont, QPainterPath, QPen,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel
import qtawesome as qta

from ..theme import PRIMARY, SECONDARY, ACCENT, TEXT, TEXT_MUTED


def add_shadow(widget, blur: int = 40, y: int = 12, color=None, alpha: int = 90):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    c = QColor(color) if color else QColor(0, 0, 0)
    c.setAlpha(alpha)
    effect.setColor(c)
    widget.setGraphicsEffect(effect)
    return effect


def icon(name: str, color: str = TEXT, size: int = 18):
    return qta.icon(name, color=color)


def gradient_pixmap(width: int, height: int, colors=None, radius: int = 16,
                    icon_name: str | None = None, icon_color: str = "#FFFFFF"):
    """Draw a rounded gradient pixmap used as a fake thumbnail."""
    if not colors:
        colors = [PRIMARY, SECONDARY]
    pm = QPixmap(width, height)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, radius, radius)
    p.setClipPath(path)

    grad = QLinearGradient(0, 0, width, height)
    grad.setColorAt(0.0, QColor(colors[0]))
    grad.setColorAt(1.0, QColor(colors[-1]))
    p.fillRect(0, 0, width, height, QBrush(grad))

    # subtle noise-ish overlay: diagonal lines
    p.setPen(QPen(QColor(255, 255, 255, 18), 1))
    for i in range(-height, width, 14):
        p.drawLine(i, 0, i + height, height)

    # play icon glyph
    if icon_name is None:
        icon_name = "fa6s.play"
    try:
        ic = qta.icon(icon_name, color=icon_color)
        pm_ic = ic.pixmap(QSize(min(width, height) // 3, min(width, height) // 3))
        p.drawPixmap(
            QPoint((width - pm_ic.width()) // 2, (height - pm_ic.height()) // 2),
            pm_ic,
        )
    except Exception:
        pass

    p.end()
    return pm


def avatar_pixmap(letter: str, size: int = 36):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor(PRIMARY))
    grad.setColorAt(1.0, QColor(SECONDARY))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, size, size)
    f = QFont()
    f.setBold(True)
    f.setPointSize(int(size * 0.42))
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, letter.upper())
    p.end()
    return pm


def logo_pixmap(size: int = 34):
    """Fluxe logo — rounded square with gradient wave."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor(PRIMARY))
    grad.setColorAt(0.5, QColor(SECONDARY))
    grad.setColorAt(1.0, QColor(ACCENT))
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, size * 0.28, size * 0.28)
    p.fillPath(path, QBrush(grad))

    # inner wave/spark
    p.setPen(QPen(QColor(255, 255, 255, 220), max(1, size // 14)))
    m = size
    p.drawLine(int(m * 0.28), int(m * 0.62), int(m * 0.44), int(m * 0.42))
    p.drawLine(int(m * 0.44), int(m * 0.42), int(m * 0.58), int(m * 0.58))
    p.drawLine(int(m * 0.58), int(m * 0.58), int(m * 0.74), int(m * 0.38))
    p.end()
    return pm
