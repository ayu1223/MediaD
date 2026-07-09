"""
Application sidebar.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta

from app.core.constants import SIDEBAR_WIDTH


class Sidebar(QWidget):
    """
    Left navigation sidebar.
    """

    page_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.buttons: list[QPushButton] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Build sidebar UI.
        """

        self.setFixedWidth(SIDEBAR_WIDTH)

        self.setStyleSheet("""
        QWidget{
            background:#2B2D31;
        }

        QPushButton{
            background:transparent;
            color:white;
            border:none;
            text-align:left;
            padding:14px 18px;
            font-size:14px;
        }

        QPushButton:hover{
            background:#3A3C43;
        }

        QPushButton:checked{
            background:#5865F2;
        }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 15, 8, 15)

        layout.setSpacing(6)

        self._add_button(
            layout,
            "Home",
            "fa6s.house",
            0,
        )

        self._add_button(
            layout,
            "Downloads",
            "fa6s.download",
            1,
        )

        self._add_button(
            layout,
            "Playlist",
            "fa6s.list",
            2,
        )

        self._add_button(
            layout,
            "History",
            "fa6s.clock-rotate-left",
            3,
        )

        self._add_button(
            layout,
            "Settings",
            "fa6s.gear",
            4,
        )

        self._add_button(
            layout,
            "About",
            "fa6s.circle-info",
            5,
        )

        layout.addStretch()

        self.buttons[0].setChecked(True)

    def _add_button(
        self,
        layout: QVBoxLayout,
        text: str,
        icon_name: str,
        page_index: int,
    ) -> None:
        """
        Add a navigation button.
        """

        button = QPushButton(
            qta.icon(
                icon_name,
                color="white",
            ),
            text,
        )

        button.setCheckable(True)

        button.setCursor(Qt.PointingHandCursor)

        button.clicked.connect(
            lambda _, idx=page_index: self._button_clicked(idx)
        )

        layout.addWidget(button)

        self.buttons.append(button)

    def _button_clicked(
        self,
        page_index: int,
    ) -> None:
        """
        Handle button click.
        """

        for index, button in enumerate(self.buttons):
            button.setChecked(index == page_index)

        self.page_changed.emit(page_index)