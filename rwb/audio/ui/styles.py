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

# Colors - Keep only functional colors
COLOR_PRIMARY = "#4CAF50"       # Green - primary brand color
COLOR_SECONDARY = "#f44336"     # Red for recording/stop actions
COLOR_GRAY_DARK = None          # Use system default
COLOR_GRAY_MEDIUM = None        # Use system default
COLOR_GRAY_LIGHT = None         # Use system default
COLOR_HIGHLIGHT = "#4CAF50"     # Green highlight for selected items
COLOR_HOVER = None              # Use system default
COLOR_BABY_BLUE = "#2196F3"     # Blue for send button
COLOR_GRAY_VERY_LIGHT = None    # Use system default
COLOR_GRAY_LIGHTER = None       # Use system default

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
# BUTTON_STYLE_NORMAL = """
#     QPushButton {
#         background-color: #4CAF50;
#         color: white;
#         border: none;
#         padding: 15px 30px;
#         font-size: 16px;
#         border-radius: 10px;
#     }
#     QPushButton:pressed {
#         background-color: #45a049;
#     }
#     QPushButton:disabled {
#         background-color: COLOR_GRAY_MEDIUM;
#     }
# """

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

# Mute button style
BUTTON_STYLE_MUTE = """
    QPushButton {
        background-color: #e0e0e0;
        border-radius: 20px;
        min-width: 40px;
        min-height: 40px;
    }
    QPushButton:hover {
        background-color: #d0d0d0;
    }
    QPushButton:pressed {
        background-color: #c0c0c0;
    }
"""

# Settings button style
SETTINGS_BUTTON_STYLE = """
    QPushButton {
        border-radius: 16px;
    }
"""

# Tab widget styles - mostly default with minimal styling
TAB_WIDGET_STYLE = """
    QTabBar {
        alignment: left;  /* Align tabs to the left */
    }
    QTabBar::tab:selected {
        border-bottom: 2px solid #4CAF50;  /* Green highlight on bottom - functional element */
    }
"""

# Splitter styles
SPLITTER_STYLE = """
    QSplitter::handle {
        width: 2px;
        margin: 2px;
    }
"""


# Text input style - keeping the rounded corners as requested
TEXT_INPUT_STYLE = """
    QTextEdit {
        border-radius: 15px;
        padding: 10px;
    }
"""

# Send button style - simplified but kept border radius
SEND_BUTTON_STYLE = """
    QPushButton {
        border-radius: 8px;
    }
"""

# Status label style
STATUS_LABEL_STYLE = """
    QLabel {
        font-size: 14px;
    }
"""

# Chat message styles
MESSAGE_USER_STYLE = """
    QFrame {
        border-radius: 15px;
        padding: 10px;
    }
"""

MESSAGE_SYSTEM_STYLE = """
    QFrame {
        border-radius: 15px;
        padding: 10px;
    }
"""

# List widget style
LIST_WIDGET_STYLE = """
    QListWidget {
        border-radius: 10px;
        padding: 8px;
    }
    QListWidget::item {
        padding: 12px;
        border-radius: 8px;
        margin: 6px 0px;
    }
    QListWidget::item:selected {
        border-left: 3px solid #4CAF50;
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

# Refresh button style - simplified to default styling
REFRESH_BUTTON_STYLE = """
    QPushButton {
        border-radius: 10px;
        padding: 8px;
        font-weight: bold;
    }
"""