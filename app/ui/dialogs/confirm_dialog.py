from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget | None, title: str, message: str) -> bool:
    """Show a Yes/No confirmation dialog and return True if the user chose Yes."""
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes


def show_error(parent: QWidget | None, title: str, message: str) -> None:
    """Show a blocking error dialog."""
    QMessageBox.critical(parent, title, message)
