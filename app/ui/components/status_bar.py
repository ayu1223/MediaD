"""Floating status bar with a small pulsing indicator."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from ..theme import SUCCESS, TEXT_MUTED, TEXT
from .helpers import add_shadow


class PulseDot(QWidget):
    def __init__(self, color: str = SUCCESS, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._color = QColor(color)
        self._alpha = 90
        self._growing = True
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
        self._t.start(40)

    def setColor(self, color: str):
        self._color = QColor(color)
        self.update()

    def _tick(self):
        if self._growing:
            self._alpha += 6
            if self._alpha >= 200:
                self._growing = False
        else:
            self._alpha -= 6
            if self._alpha <= 90:
                self._growing = True
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # halo
        halo = QColor(self._color)
        halo.setAlpha(self._alpha)
        p.setBrush(QBrush(halo))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 12, 12)
        # core
        p.setBrush(QBrush(self._color))
        p.drawEllipse(4, 4, 6, 6)
        p.end()


class StatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(12)

        self.dot = PulseDot(SUCCESS)
        lay.addWidget(self.dot)

        self.text_lbl = QLabel("Ready")
        self.text_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600;")
        lay.addWidget(self.text_lbl)

        sep = QLabel("•")
        sep.setStyleSheet(f"color: {TEXT_MUTED};")
        lay.addWidget(sep)

        self.hint_lbl = QLabel("No active downloads")
        self.hint_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        lay.addWidget(self.hint_lbl)

        lay.addStretch()

        self.right_lbl = QLabel("v1.0.0  ·  Fluxe")
        self.right_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        lay.addWidget(self.right_lbl)

        add_shadow(self, blur=30, y=8, alpha=100)

    def setStatus(self, text: str, hint: str = "", color: str = SUCCESS):
        self.text_lbl.setText(text)
        self.hint_lbl.setText(hint)
        self.dot.setColor(color)
