from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.logger import configure_logging, get_logger
from app.core.version import APP_NAME, APP_VERSION
from app.ui.main_window import MainWindow

_logger = get_logger(__name__)


def main() -> int:
    """Launch the Media Downloader application."""
    configure_logging()
    _logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

    app = QApplication(sys.argv)
    # MainWindow applies its own stylesheet (migrated Fluxe design, see
    # app/ui/theme.py) in its constructor, so no theme is applied here.

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    _logger.info("%s exited with code %d", APP_NAME, exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
