"""About page — hero, description, links, libraries.

Visual design migrated from the Fluxe UI prototype; version/author come from the
real app.core.version module. The pulsing-logo animation includes a visibility
guard (see AnimatedLogo) discovered necessary during an earlier QPainter-warning
audit of this exact component: QPropertyAnimation.stop() emits finished() in this
Qt build even on manual stop, which without the guard would immediately restart
the ping-pong animation via _flip() right after hiding the page.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
import qtawesome as qta

from app.core.version import APP_AUTHOR, APP_NAME, APP_VERSION
from ..theme import TEXT, TEXT_MUTED, PRIMARY, SECONDARY, ACCENT
from ..components.cards import GlassCard
from ..components.buttons import PrimaryButton, SecondaryButton
from ..components.helpers import logo_pixmap, add_shadow

_LIBRARIES = [
    ("PySide6", "Qt for Python — cross-platform toolkit"),
    ("yt-dlp", "Media extraction and download engine"),
    ("qtawesome", "Icon font library"),
]


class AnimatedLogo(QLabel):
    def __init__(self, size: int = 96, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setPixmap(logo_pixmap(size))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shadow = add_shadow(self, blur=44, y=0, color=QColor(PRIMARY), alpha=180)

        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(1600)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setStartValue(30)
        self._anim.setEndValue(70)
        self._anim.setLoopCount(-1)
        self._anim.finished.connect(self._flip)
        self._forward = True

    def _flip(self):
        if not self.isVisible():
            return
        self._forward = not self._forward
        s, e = (30, 70) if self._forward else (70, 30)
        self._anim.setStartValue(s)
        self._anim.setEndValue(e)
        self._anim.start()

    def showEvent(self, e):
        super().showEvent(e)
        if self._anim.state() != QPropertyAnimation.State.Running:
            self._anim.start()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._anim.stop()


class LinkCard(QFrame):
    def __init__(self, icon_name: str, title: str, subtitle: str, color: str, url: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._url = url
        add_shadow(self, blur=28, y=10, alpha=80)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(14)

        ic = QLabel()
        ic.setFixedSize(42, 42)
        ic.setStyleSheet(f"background: {color}22; border-radius: 12px;")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setPixmap(qta.icon(icon_name, color=color).pixmap(20, 20))
        lay.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {TEXT}; font-weight: 600;")
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        col.addWidget(t)
        col.addWidget(s)
        lay.addLayout(col, 1)

        arrow = QLabel()
        arrow.setPixmap(qta.icon("fa6s.arrow-up-right-from-square", color=TEXT_MUTED).pixmap(14, 14))
        lay.addWidget(arrow)

    def mouseReleaseEvent(self, event):
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))
        super().mouseReleaseEvent(event)


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(32, 24, 32, 32)
        outer.setSpacing(22)

        hero = GlassCard(elevated=True, padding=36)
        hero.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero.layout().setSpacing(12)

        logo_wrap = QWidget()
        lw = QHBoxLayout(logo_wrap)
        lw.setContentsMargins(0, 0, 0, 0)
        lw.addStretch()
        lw.addWidget(AnimatedLogo(96))
        lw.addStretch()
        hero.layout().addWidget(logo_wrap)

        name = QLabel(APP_NAME)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"color: {TEXT}; font-size: 40px; font-weight: 800; letter-spacing: -1px;")
        hero.layout().addWidget(name)

        ver = QLabel(f"Version {APP_VERSION}")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {ACCENT}; letter-spacing: 1px; font-size: 12px; font-weight: 700;")
        hero.layout().addWidget(ver)

        desc = QLabel("A modern desktop workspace for downloading and managing supported online media.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; max-width: 520px;")
        hero.layout().addWidget(desc)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()
        check_btn = PrimaryButton("Check for updates", icon_name="fa6s.arrows-rotate")
        actions.addWidget(check_btn)
        actions.addStretch()
        aw = QWidget()
        aw.setLayout(actions)
        hero.layout().addWidget(aw)

        outer.addWidget(hero)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        links = [
            ("fa6s.book", "Documentation", "Guides & how-tos", PRIMARY, ""),
            ("fa6b.github", "Source code", "View project on GitHub", SECONDARY, ""),
            ("fa6s.envelope", "Contact", APP_AUTHOR, ACCENT, ""),
            ("fa6s.heart", "Support", "Support this project", "#F87171", ""),
        ]
        for i, (icon_name, title, subtitle, color, url) in enumerate(links):
            grid.addWidget(LinkCard(icon_name, title, subtitle, color, url), i // 2, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)

        libs = GlassCard(padding=22)
        h = QLabel("Built with")
        h.setObjectName("SectionHeader")
        libs.layout().addWidget(h)
        muted = QLabel("This app stands on the shoulders of these open source projects.")
        muted.setObjectName("MutedLabel")
        libs.layout().addWidget(muted)

        for lib_name, sub in _LIBRARIES:
            row = QHBoxLayout()
            row.setSpacing(12)
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {PRIMARY}; border-radius: 4px;")
            row.addWidget(dot)
            n = QLabel(lib_name)
            n.setStyleSheet(f"color: {TEXT}; font-weight: 600; min-width: 120px;")
            row.addWidget(n)
            s = QLabel(sub)
            s.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            row.addWidget(s)
            row.addStretch()
            w = QWidget()
            w.setLayout(row)
            libs.layout().addWidget(w)

        outer.addWidget(libs)

        credits = QLabel(f"Crafted by {APP_AUTHOR}")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet(f"color: {TEXT_MUTED}; padding-top: 8px;")
        outer.addWidget(credits)

        outer.addStretch()
        scroll.setWidget(content)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)
