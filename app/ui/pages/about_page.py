"""
About page.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AboutPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(
                "Media Downloader\nVersion 1.0.0"
            )
        )