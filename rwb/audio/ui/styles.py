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
        background-color: #2d2d2d;
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

# Scroll area style
SCROLL_AREA_STYLE = """
    QScrollArea {
        border: none;
        background-color: #1e1e1e;
    }
    QScrollBar:vertical {
        border: none;
        background: #2d2d2d;
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

# Status label style
STATUS_LABEL_STYLE = """
    QLabel {
        color: #cccccc;
        font-size: 14px;
    }
"""

# Chat container style
CHAT_CONTAINER_STYLE = "background-color: #1e1e1e;" 