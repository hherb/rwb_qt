"""UI components module.

This module contains reusable UI components used throughout the application.
"""

from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QColor, QPalette

from .styles import (
    BUTTON_STYLE_NORMAL,
    BUTTON_STYLE_RECORDING,
    BUTTON_STYLE_STOP,
    SCROLL_AREA_STYLE,
    STATUS_LABEL_STYLE,
    CHAT_CONTAINER_STYLE,
    BUTTON_TALK,
    STATUS_READY,
    MIC_BODY_STYLE,
    MIC_BASE_STYLE,
    TEXT_INPUT_STYLE,
    SEND_BUTTON_STYLE
)

def create_status_label() -> QLabel:
    """Create a status label widget.
    
    Returns:
        QLabel: The configured status label
    """
    label = QLabel(STATUS_READY)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(STATUS_LABEL_STYLE)
    return label

def create_talk_button() -> QPushButton:
    """Create a talk button widget with a microphone icon.
    
    Returns:
        QPushButton: The configured talk button with microphone icon
    """
    button = QPushButton()
    button.setIcon(QIcon("rwb/icons/sst_green.png"))
    button.setIconSize(QSize(32, 32))
    button.setToolTip("Hold to talk")
    button.setStyleSheet("""
        QPushButton {
            background-color: #e0e0e0;
            border-radius: 37px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
    """)
    return button

def create_stop_button() -> QPushButton:
    """Create a stop button widget.
    
    Returns:
        QPushButton: The configured stop button
    """
    button = QPushButton()
    button.setIcon(QIcon("rwb/icons/stop_red.png"))
    button.setIconSize(QSize(24, 24))
    button.setToolTip("Stop processing")
    button.setStyleSheet("""
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
    """)
    button.setFixedSize(40, 40)
    button.setVisible(False)
    return button

def create_text_input() -> QTextEdit:
    """Create a text input widget.
    
    Returns:
        QTextEdit: The configured text input
    """
    input_field = QTextEdit()
    input_field.setPlaceholderText("Type your message here...")
    input_field.setFixedHeight(75)  # 3 lines height
    input_field.setAcceptRichText(False)
    input_field.setStyleSheet("""
        QTextEdit {
            background-color: #f0f0f0;
            color: #333333;
            border: none;
            border-radius: 20px;
            padding: 15px;
            selection-background-color: #4CAF50;
        }
    """)
    return input_field

def create_send_button() -> QPushButton:
    """Create a send button widget.
    
    Returns:
        QPushButton: The configured send button
    """
    button = QPushButton()
    button.setIcon(QIcon("rwb/icons/send_blue.png"))
    button.setIconSize(QSize(24, 24))
    button.setToolTip("Send message")
    button.setStyleSheet("""
        QPushButton {
            background-color: #e0e0e0;
            border-radius: 20px;
            min-width: 40px;
            min-height: 40px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
    """)
    return button

def create_chat_scroll_area() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    """Create a scroll area for chat messages.
    
    Returns:
        tuple: A tuple containing (scroll_area, chat_container, chat_layout)
    """
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
    
    chat_container = QWidget()
    chat_layout = QVBoxLayout(chat_container)
    chat_layout.setAlignment(Qt.AlignTop)
    chat_layout.setSpacing(10)
    chat_container.setStyleSheet(CHAT_CONTAINER_STYLE)
    
    scroll_area.setWidget(chat_container)
    return scroll_area, chat_container, chat_layout

def create_button_layout(parent: QWidget) -> QHBoxLayout:
    """Create a layout for buttons.
    
    Args:
        parent: The parent widget for the layout
        
    Returns:
        QHBoxLayout: The button layout
    """
    layout = QHBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout 