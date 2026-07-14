# theme.py

""""Design tokens & global stylesheet for Fluxe."""

# ------- Color palette (per spec) -------
BG = "#0D1117"
CARD = "#161B22"
ELEVATED = "#1E2430"
SIDEBAR_BG = "#11161F"

PRIMARY = "#7C5CFF"
SECONDARY = "#5EA2FF"
ACCENT = "#56D8FF"

SUCCESS = "#4ADE80"
WARNING = "#FBBF24"
DANGER = "#F87171"

TEXT = "#E6EDF3"
TEXT_MUTED = "#8B96A8"
TEXT_DIM = "#5C6675"
BORDER = "#242C3B"
BORDER_SOFT = "#1B2230"

# ------- Radii & spacing -------
RADIUS_SM = 10
RADIUS_MD = 16
RADIUS_LG = 22
RADIUS_XL = 28
GAP = 20
GAP_LG = 28

# ------- Typography -------
FONT_FAMILY = "'Segoe UI', 'SF Pro Display', 'Inter', 'DejaVu Sans', sans-serif"


def build_stylesheet() -> str:
    return f"""
    /* ---------- Base ---------- */
    QWidget {{
        color: {TEXT};
        font-family: {FONT_FAMILY};
        font-size: 14px;
        background: transparent;
    }}

    QMainWindow, #RootBackground {{
        background: {BG};
    }}

    QToolTip {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
    }}

    /* ---------- Scrollbars ---------- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 6px 2px 6px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 5px;
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {TEXT_DIM}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px 6px 2px 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 5px;
        min-width: 40px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {TEXT_DIM}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ---------- Sidebar ---------- */
    #Sidebar {{
        background: {SIDEBAR_BG};
        border-right: 1px solid {BORDER_SOFT};
    }}
    QPushButton#NavButton {{
        background: transparent;
        color: {TEXT_MUTED};
        border: none;
        border-radius: 14px;
        padding: 12px 16px;
        text-align: left;
        font-size: 14px;
        font-weight: 500;
    }}
    QPushButton#NavButton:hover {{
        background: rgba(124, 92, 255, 0.08);
        color: {TEXT};
    }}
    QPushButton#NavButton[active="true"] {{
        background: rgba(124, 92, 255, 0.16);
        color: {TEXT};
        font-weight: 600;
    }}

    /* ---------- Top bar ---------- */
    #TopBar {{
        background: {BG};
        border-bottom: 1px solid {BORDER_SOFT};
    }}
    #Logo {{
        color: {TEXT};
        font-weight: 700;
        font-size: 18px;
        letter-spacing: 0.3px;
    }}
    QPushButton#IconBtn {{
        background: {CARD};
        border: 1px solid {BORDER_SOFT};
        border-radius: 12px;
        padding: 8px;
    }}
    QPushButton#IconBtn:hover {{
        background: {ELEVATED};
        border: 1px solid {BORDER};
    }}
    QLabel#Avatar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {PRIMARY}, stop:1 {SECONDARY});
        color: white;
        border-radius: 18px;
        font-weight: 700;
    }}

    /* ---------- Status bar ---------- */
    #StatusBar {{
        background: {CARD};
        border: 1px solid {BORDER_SOFT};
        border-radius: 14px;
    }}

    /* ---------- Cards ---------- */
    QFrame#GlassCard {{
        background: {CARD};
        border: 1px solid {BORDER_SOFT};
        border-radius: {RADIUS_LG}px;
    }}
    QFrame#GlassCard[elevated="true"] {{
        background: {ELEVATED};
    }}
    QFrame#StatCard {{
        background: {CARD};
        border: 1px solid {BORDER_SOFT};
        border-radius: 18px;
    }}
    QFrame#StatCard:hover {{
        border: 1px solid rgba(124, 92, 255, 0.5);
    }}

    /* ---------- Typography helpers ---------- */
    QLabel#PageTitle {{
        color: {TEXT};
        font-size: 30px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }}
    QLabel#PageSubtitle {{
        color: {TEXT_MUTED};
        font-size: 14px;
    }}
    QLabel#SectionHeader {{
        color: {TEXT};
        font-size: 16px;
        font-weight: 600;
    }}
    QLabel#CaptionLabel {{
        color: {TEXT_DIM};
        font-size: 12px;
    }}
    QLabel#MutedLabel {{
        color: {TEXT_MUTED};
        font-size: 13px;
    }}
    QLabel#Heading {{
        color: {TEXT};
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#BigNumber {{
        color: {TEXT};
        font-size: 28px;
        font-weight: 700;
    }}

    /* ---------- Buttons ---------- */
    QPushButton#PrimaryBtn {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY}, stop:1 {SECONDARY});
        color: white;
        border: none;
        border-radius: 14px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton#PrimaryBtn:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #8B6EFF, stop:1 #6FB0FF);
    }}
    QPushButton#PrimaryBtn:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6A4EE5, stop:1 #4A8EE5);
    }}
    QPushButton#PrimaryBtn:disabled {{
        background: {BORDER};
        color: {TEXT_DIM};
    }}

    QPushButton#SecondaryBtn {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 12px 22px;
        font-weight: 500;
    }}
    QPushButton#SecondaryBtn:hover {{
        background: #262E3D;
        border: 1px solid #33405A;
    }}

    QPushButton#DangerBtn {{
        background: rgba(248, 113, 113, 0.12);
        color: {DANGER};
        border: 1px solid rgba(248, 113, 113, 0.3);
        border-radius: 14px;
        padding: 10px 20px;
        font-weight: 600;
    }}
    QPushButton#DangerBtn:hover {{
        background: rgba(248, 113, 113, 0.2);
    }}

    QPushButton#GhostBtn {{
        background: transparent;
        color: {TEXT_MUTED};
        border: none;
        border-radius: 12px;
        padding: 8px 14px;
    }}
    QPushButton#GhostBtn:hover {{
        background: {ELEVATED};
        color: {TEXT};
    }}

    QPushButton#ChipBtn {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER_SOFT};
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton#ChipBtn:hover {{
        border: 1px solid {PRIMARY};
        color: {TEXT};
    }}

    /* ---------- Inputs ---------- */
    QLineEdit#ModernInput {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 12px 16px;
        font-size: 14px;
        selection-background-color: {PRIMARY};
    }}
    QLineEdit#ModernInput:focus {{
        border: 1px solid {PRIMARY};
        background: #212938;
    }}
    QLineEdit#ModernInput::placeholder {{
        color: {TEXT_DIM};
    }}

    QLineEdit#SearchInput {{
        background: {CARD};
        color: {TEXT};
        border: 1px solid {BORDER_SOFT};
        border-radius: 12px;
        padding: 9px 14px 9px 34px;
    }}
    QLineEdit#SearchInput:focus {{
        border: 1px solid {PRIMARY};
    }}

    QComboBox#ModernCombo {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 10px 14px;
        min-width: 140px;
    }}
    QComboBox#ModernCombo:hover {{ border: 1px solid {PRIMARY}; }}
    QComboBox#ModernCombo::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox#ModernCombo::down-arrow {{
        image: none;
    }}
    QComboBox QAbstractItemView {{
        background: {ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 6px;
        selection-background-color: rgba(124, 92, 255, 0.2);
        outline: 0;
    }}

    /* ---------- Checkboxes ---------- */
    QCheckBox {{
        color: {TEXT};
        spacing: 10px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 1.5px solid {BORDER};
        background: {ELEVATED};
    }}
    QCheckBox::indicator:hover {{
        border: 1.5px solid {PRIMARY};
    }}
    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {PRIMARY}, stop:1 {SECONDARY});
        border: 1.5px solid {PRIMARY};
        image: none;
    }}

    /* ---------- Progress bar ---------- */
    QProgressBar#ModernProgress {{
        background: {ELEVATED};
        border: none;
        border-radius: 5px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar#ModernProgress::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY}, stop:0.5 {SECONDARY}, stop:1 {ACCENT});
        border-radius: 5px;
    }}

    /* ---------- Slider ---------- */
    QSlider::groove:horizontal {{
        background: {ELEVATED};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PRIMARY}, stop:1 {SECONDARY});
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: white;
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {ACCENT};
    }}

    /* ---------- Frame separators ---------- */
    QFrame#Separator {{
        background: {BORDER_SOFT};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}
    """
