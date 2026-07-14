"""Top bar with logo, global search and actions."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget, QSizePolicy

from ..theme import TEXT
from .inputs import SearchBox
from .buttons import IconButton


class TopBar(QFrame):
    sidebarToggle = Signal()
    themeToggle = Signal()
    settingsRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(66)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 12, 22, 12)
        lay.setSpacing(14)

        # collapse / expand sidebar
        self.toggle_btn = IconButton("fa6s.bars", tooltip="Toggle sidebar")
        self.toggle_btn.clicked.connect(self.sidebarToggle.emit)
        lay.addWidget(self.toggle_btn)

        # section title (updated by MainWindow)
        self.title_lbl = QLabel("Home")
        self.title_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 16px;")
        lay.addWidget(self.title_lbl)

        lay.addStretch()

        # search
        self.search = SearchBox(placeholder="Search anywhere…")
        self.search.setMinimumWidth(340)
        self.search.setMaximumWidth(420)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay.addWidget(self.search)

        # actions
        self.theme_btn = IconButton("fa6s.moon", tooltip="Toggle theme")
        self.theme_btn.clicked.connect(self.themeToggle.emit)
        lay.addWidget(self.theme_btn)

        self.notif_btn = IconButton("fa6s.bell", tooltip="Notifications")
        lay.addWidget(self.notif_btn)

        self.settings_btn = IconButton("fa6s.gear", tooltip="Settings")
        self.settings_btn.clicked.connect(self.settingsRequested.emit)
        lay.addWidget(self.settings_btn)

        # avatar
        av = QLabel("F")
        av.setObjectName("Avatar")
        av.setFixedSize(36, 36)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(av)

    def setSectionTitle(self, title: str):
        self.title_lbl.setText(title)
