"""Sidebar with animated active indicator and collapse support."""
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy,
)
import qtawesome as qta

from ..theme import TEXT, TEXT_MUTED, PRIMARY, SECONDARY
from .helpers import logo_pixmap

NAV_ITEMS = [
    ("home", "Home", "fa6s.house"),
    ("playlist", "Playlist", "fa6s.list-ul"),
    ("downloads", "Downloads", "fa6s.download"),
    ("history", "History", "fa6s.clock-rotate-left"),
    ("settings", "Settings", "fa6s.gear"),
    ("about", "About", "fa6s.circle-info"),
]


class NavButton(QPushButton):
    def __init__(self, key: str, label: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.label = label
        self.icon_name = icon_name
        self.setObjectName("NavButton")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setIconSize(QSize(18, 18))
        self._refresh_icon(False)
        self.setText(f"  {label}")

    def _refresh_icon(self, active: bool):
        col = TEXT if active else TEXT_MUTED
        self.setIcon(qta.icon(self.icon_name, color=col))

    def setActive(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self._refresh_icon(active)


class Sidebar(QFrame):
    navigated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(240)
        self._collapsed = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 22, 18, 22)
        outer.setSpacing(18)

        # ---------- Header: logo + name + collapse ----------
        header = QHBoxLayout()
        header.setSpacing(10)

        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(logo_pixmap(34))
        self.logo_lbl.setFixedSize(34, 34)
        header.addWidget(self.logo_lbl)

        self.name_lbl = QLabel("Fluxe")
        self.name_lbl.setObjectName("Logo")
        header.addWidget(self.name_lbl)
        header.addStretch()

        outer.addLayout(header)

        # small caption
        self.caption = QLabel("MEDIA WORKSPACE")
        self.caption.setStyleSheet("color: #5C6675; font-size: 10px; font-weight: 700; letter-spacing: 1.4px;")
        outer.addWidget(self.caption)

        # ---------- Nav ----------
        self.buttons: dict[str, NavButton] = {}
        nav_wrap = QVBoxLayout()
        nav_wrap.setSpacing(6)
        for key, label, icon_name in NAV_ITEMS:
            b = NavButton(key, label, icon_name)
            b.clicked.connect(lambda _=False, k=key: self._on_click(k))
            nav_wrap.addWidget(b)
            self.buttons[key] = b
        outer.addLayout(nav_wrap)

        outer.addStretch()

        # ---------- Footer: user card ----------
        footer = QFrame()
        footer.setStyleSheet(
            "background: rgba(124,92,255,0.08);"
            "border: 1px solid rgba(124,92,255,0.18);"
            "border-radius: 14px;"
        )
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(10)

        av = QLabel("F")
        av.setObjectName("Avatar")
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(av)

        info = QVBoxLayout()
        info.setSpacing(0)
        n = QLabel("Fluxe Pro")
        n.setStyleSheet(f"color: {TEXT}; font-weight: 600;")
        e = QLabel("Free plan")
        e.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        info.addWidget(n)
        info.addWidget(e)
        fl.addLayout(info)
        fl.addStretch()

        outer.addWidget(footer)

        # animate width for collapse
        self._anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim2 = QPropertyAnimation(self, b"maximumWidth", self)
        self._anim2.setDuration(220)
        self._anim2.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _on_click(self, key: str):
        self.setActive(key)
        self.navigated.emit(key)

    def setActive(self, key: str):
        for k, b in self.buttons.items():
            b.setActive(k == key)

    def toggleCollapsed(self):
        self._collapsed = not self._collapsed
        target = 76 if self._collapsed else 240
        self._anim.stop(); self._anim2.stop()
        self._anim.setStartValue(self.width()); self._anim.setEndValue(target)
        self._anim2.setStartValue(self.width()); self._anim2.setEndValue(target)
        self._anim.start(); self._anim2.start()

        self.name_lbl.setVisible(not self._collapsed)
        self.caption.setVisible(not self._collapsed)
        for b in self.buttons.values():
            b.setText("" if self._collapsed else f"  {b.label}")
