"""Modern input widgets: line edit, combo, switch, search."""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, Property, Signal
from PySide6.QtGui import QPainter, QColor, QCursor, QBrush, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QLineEdit, QComboBox, QWidget, QHBoxLayout, QLabel, QSizePolicy,
)
import qtawesome as qta

from ..theme import PRIMARY, SECONDARY, BORDER, ELEVATED, TEXT_DIM


class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ModernInput")
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(46)


class ModernComboBox(QComboBox):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCombo")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if items:
            self.addItems(items)


class SearchBox(QWidget):
    textChanged = Signal(str)

    def __init__(self, placeholder: str = "Search…", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.edit = QLineEdit()
        self.edit.setObjectName("SearchInput")
        self.edit.setPlaceholderText(placeholder)
        self.edit.setMinimumHeight(38)
        self.edit.textChanged.connect(self.textChanged.emit)
        lay.addWidget(self.edit)

        # icon overlay
        self.icon_lbl = QLabel(self.edit)
        self.icon_lbl.setPixmap(qta.icon("fa6s.magnifying-glass", color="#8B96A8").pixmap(14, 14))
        self.icon_lbl.setStyleSheet("background: transparent;")
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.move(12, 11)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # keep icon vertically centred
        self.icon_lbl.move(12, (self.edit.height() - 16) // 2)

    def text(self) -> str:
        return self.edit.text()


class ModernSwitch(QWidget):
    """Animated iOS-style toggle switch."""
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 22.0 if checked else 2.0
        self.setFixedSize(46, 26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_pos(self):
        return self._pos

    def _set_pos(self, v):
        self._pos = float(v)
        self.update()

    pos = Property(float, _get_pos, _set_pos)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(22.0 if checked else 2.0)
        self._anim.start()
        self.toggled.emit(checked)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())

        # bg
        if self._checked:
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0.0, QColor(PRIMARY))
            grad.setColorAt(1.0, QColor(SECONDARY))
            p.setBrush(QBrush(grad))
        else:
            p.setBrush(QColor(ELEVATED))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawRoundedRect(r, 13, 13)

        # knob
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(self._pos, 2, 22, 22))
        p.end()
