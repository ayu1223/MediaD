import sys

from PySide6.QtWidgets import QApplication

from app.core.theme import APP_STYLE
from app.ui.main_window import MainWindow


def main() -> None:

    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()