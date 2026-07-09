"""
History page.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HistoryPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Download History")
        )