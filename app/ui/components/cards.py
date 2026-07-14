"""Cards: base GlassCard + specialized StatCard."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
import qtawesome as qta

from ..theme import TEXT_MUTED, TEXT
from .helpers import add_shadow


class GlassCard(QFrame):
    def __init__(self, parent=None, elevated: bool = False, padding: int = 22):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        if elevated:
            self.setProperty("elevated", "true")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(14)
        add_shadow(self, blur=40, y=16, color=QColor(0, 0, 0), alpha=110)

    def layout(self):  # type: ignore[override]
        return self._layout


class StatCard(QFrame):
    def __init__(self, label: str, value: str, hint: str = "", icon_name: str = "fa6s.chart-simple",
                 color: str = "#7C5CFF", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(120)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(10)

        icon_box = QLabel()
        icon_box.setFixedSize(38, 38)
        icon_box.setStyleSheet(
            f"background: {color}22; border-radius: 12px;"
        )
        pm = qta.icon(icon_name, color=color).pixmap(20, 20)
        icon_box.setPixmap(pm)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(icon_box)

        label_lbl = QLabel(label)
        label_lbl.setObjectName("MutedLabel")
        top.addWidget(label_lbl)
        top.addStretch()

        outer.addLayout(top)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("BigNumber")
        outer.addWidget(value_lbl)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("CaptionLabel")
            outer.addWidget(hint_lbl)

        outer.addStretch()
        add_shadow(self, blur=30, y=10, alpha=90)


class SectionCard(GlassCard):
    """Card with a title header and optional description."""
    def __init__(self, title: str, description: str = "", parent=None, elevated=False):
        super().__init__(parent, elevated=elevated, padding=24)
        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 6)
        header.setSpacing(4)

        t = QLabel(title)
        t.setObjectName("SectionHeader")
        header.addWidget(t)

        if description:
            d = QLabel(description)
            d.setObjectName("MutedLabel")
            d.setWordWrap(True)
            header.addWidget(d)

        wrap = QWidget()
        wrap.setLayout(header)
        self._layout.addWidget(wrap)

    def add(self, widget: QWidget):
        self._layout.addWidget(widget)
