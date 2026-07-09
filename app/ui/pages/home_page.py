"""
Home page.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    """
    Main dashboard page.
    """

    def __init__(self) -> None:
        super().__init__()

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Build home page UI.
        """

        layout = QVBoxLayout(self)

        layout.setAlignment(
            Qt.AlignCenter
        )

        title = QLabel(
            "Welcome to Media Downloader"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        subtitle = QLabel(
            "Download, manage and organize your media"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                color: #aaaaaa;
            }
            """
        )


        layout.addWidget(title)

        layout.addWidget(subtitle)