"""
Downloads page.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DownloadsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Downloads")
        )