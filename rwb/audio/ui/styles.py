"""UI styles and constants module.

This module contains all the UI-related constants, styles, and layout configurations
used throughout the application.
"""

# Status messages
STATUS_READY = "Ready to talk"
STATUS_LISTENING = "Listening..."
STATUS_PROCESSING = "Processing your request..."
STATUS_SPEAKING = "Speaking..."
STATUS_STOPPED = "Processing stopped"

# Button text
BUTTON_TALK = "Hold to Talk"
BUTTON_RECORDING = "Recording..."
BUTTON_PROCESSING = "Processing..."

# Colors 
COLOR_PRIMARY = "#4CAF50"       # Green - primary brand color
COLOR_SECONDARY = "#f44336"     # Red for recording/stop actions
COLOR_GRAY_DARK = "#1a1a1a"     # Very dark gray (near black) - main background
COLOR_GRAY_MEDIUM = "#2d2d2d"   # Dark gray - component backgrounds
COLOR_GRAY_LIGHT = "#cccccc"    # Light gray - text color
COLOR_HIGHLIGHT = "#4CAF50"     # Green highlight for selected items
COLOR_HOVER = "#333333"         # Hover color for interactive elements

# Global tooltip style
TOOLTIP_STYLE = """
    QToolTip {
        background-color: #f0f0f0;
        color: #000000;
        border: 1px solid #707070;
        padding: 5px;
        border-radius: 3px;
        font-size: 12px;
    }
"""

# Button styles
BUTTON_STYLE_NORMAL = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton:pressed {
        background-color: #45a049;
    }
    QPushButton:disabled {
        background-color: COLOR_GRAY_MEDIUM;
    }
"""

BUTTON_STYLE_RECORDING = """
    QPushButton {
        background-color: #f44336;
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 16px;
        border-radius: 10px;
    }
    QPushButton QFrame {
        background-color: white;
    }
"""

BUTTON_STYLE_STOP = """
    QPushButton {
        background-color: #f44336;
        border: none;
        border-radius: 20px;
        padding: 4px;
    }
    QPushButton:pressed {
        background-color: #d32f2f;
    }
    QPushButton:hover {
        background-color: #e53935;
    }
"""

# Settings button style
SETTINGS_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        border: none;
        border-radius: 16px;
    }
    QPushButton:hover {
        background-color: #444444;
    }
    QPushButton:pressed {
        background-color: #555555;
    }
"""

# Tab widget styles
TAB_WIDGET_STYLE = """
    QTabWidget::pane {
        border: 1px solid #444;
        background: #1a1a1a;  /* Darker background for better contrast */
        border-radius: 5px;
    }
    QTabBar {
        alignment: left;  /* Align tabs to the left */
    }
    QTabBar::tab {
        background: COLOR_GRAY_MEDIUM;
        color: #cccccc;
        padding: 10px 20px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #383838;
        border-bottom: 2px solid #4CAF50;  /* Green highlight on bottom */
        color: white;  /* Brighter text for selected tab */
    }
    QTabBar::tab:hover {
        background: #333333;
    }
"""

# Splitter styles
SPLITTER_STYLE = """
    QSplitter::handle {
        background-color: #444;
        width: 2px;
        margin: 2px;
    }
    QSplitter::handle:hover {
        background-color: #4CAF50;
    }
"""

# Scroll area style
SCROLL_AREA_STYLE = """
    QScrollArea {
        border: none;
        background-color: #1e1e1e;
    }
    QScrollBar:vertical {
        border: none;
        background: COLOR_GRAY_MEDIUM;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #3d3d3d;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

# Chat container style
CHAT_CONTAINER_STYLE = """
    QWidget {
        background-color: #1e1e1e;
    }
"""

# Text input style
TEXT_INPUT_STYLE = """
    QTextEdit {
        background-color: #4d4d4d;
        color: white;
        border: 1px solid #3d3d3d;
        border-radius: 30px;
        padding: 10px;
        selection-background-color: #4CAF50;
    }
"""

# Send button style
SEND_BUTTON_STYLE = """
    QPushButton {
        background-color: #2196F3;
        border: none;
        border-radius: 8px;
    }
    QPushButton:hover {
        background-color: #1976D2;
    }
    QPushButton:pressed {
        background-color: #0D47A1;
    }
    QPushButton:disabled {
        background-color: #555555;
    }
"""

# Status label style
STATUS_LABEL_STYLE = """
    QLabel {
        color: #cccccc;
        font-size: 14px;
    }
"""

# Chat message styles
MESSAGE_USER_STYLE = """
    QFrame {
        background-color: #2a3236;
        border-radius: 15px;
        padding: 10px;
    }
    QLabel {
        color: white;
    }
"""

MESSAGE_SYSTEM_STYLE = """
    QFrame {
        background-color: #232a30;
        border-radius: 15px;
        padding: 10px;
    }
    QLabel {
        color: white;
    }
"""

# List widget style
LIST_WIDGET_STYLE = """
    QListWidget {
        background-color: #292929;
        border-radius: 10px;
        padding: 8px;
        border: 1px solid #3a3a3a;
        outline: none;
        selection-background-color: transparent;
        show-decoration-selected: 0;
        alternate-background-color: #313131;
    }
    QListWidget::item {
        color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        margin: 6px 0px;
        border: none;
        outline: none;
    }
    QListWidget::item:selected {
        background-color: #3d3d3d;
        border-left: 3px solid #4CAF50;
        border-top: none;
        border-right: none;
        border-bottom: none;
        outline: none;
    }
    QListWidget::item:alternate {
        background-color: #313131;
    }
    QListWidget::item:hover {
        background-color: #363636;
    }
    /* Remove separator lines */
    QListView::separator {
        height: 0px;
        background: transparent;
    }
    
    /* Make sure no focus outline appears */
    *:focus {
        outline: none;
    }
"""

# Info frame style
INFO_FRAME_STYLE = """
    QFrame {
        background-color: #333333;
        border-radius: 10px;
        padding: 5px;
    }
"""

# Icon label style
ICON_LABEL_STYLE = "font-size: 24px;"

# Microphone component styles
MIC_BODY_STYLE = """
    background-color: #4CAF50;
    border-radius: 8px;
"""

MIC_BASE_STYLE = """
    background-color: #4CAF50;
    border-radius: 4px;
"""

# Title styles
TITLE_STYLE = "font-size: 16px; font-weight: bold;"
INFO_LABEL_STYLE = "color: #cccccc;"

# Refresh button style
REFRESH_BUTTON_STYLE = """
    QPushButton {
        background-color: #3a3a3a;
        border-radius: 10px;
        padding: 8px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
"""