"""
Main application window.
"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.core.constants import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)

from app.core.version import APP

from app.ui.sidebar import Sidebar

from app.ui.pages.home_page import HomePage
from app.ui.pages.downloads_page import DownloadsPage
from app.ui.pages.playlist_page import PlaylistPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.about_page import AboutPage


class MainWindow(QMainWindow):
    """
    Main application window.
    """

    def __init__(self) -> None:
        super().__init__()

        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        """
        Configure main window properties.
        """

        self.setWindowTitle(
            f"{APP.app_name} v{APP.version}"
        )

        self.resize(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
        )

        self.setMinimumSize(
            MIN_WINDOW_WIDTH,
            MIN_WINDOW_HEIGHT,
        )

    def _setup_ui(self) -> None:
        """
        Build application UI.
        """

        central_widget = QWidget(self)

        self.setCentralWidget(
            central_widget
        )

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)


        # -----------------------------
        # Sidebar
        # -----------------------------

        self.sidebar = Sidebar()


        # -----------------------------
        # Pages
        # -----------------------------

        self.pages = QStackedWidget()


        self.home_page = HomePage()

        self.downloads_page = DownloadsPage()

        self.playlist_page = PlaylistPage()

        self.history_page = HistoryPage()

        self.settings_page = SettingsPage()

        self.about_page = AboutPage()


        self.pages.addWidget(
            self.home_page
        )

        self.pages.addWidget(
            self.downloads_page
        )

        self.pages.addWidget(
            self.playlist_page
        )

        self.pages.addWidget(
            self.history_page
        )

        self.pages.addWidget(
            self.settings_page
        )

        self.pages.addWidget(
            self.about_page
        )


        # -----------------------------
        # Connect navigation
        # -----------------------------

        self.sidebar.page_changed.connect(
            self.pages.setCurrentIndex
        )


        # -----------------------------
        # Layout
        # -----------------------------

        main_layout.addWidget(
            self.sidebar
        )

        main_layout.addWidget(
            self.pages
        )