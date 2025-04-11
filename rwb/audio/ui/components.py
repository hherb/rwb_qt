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
    QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from .styles import (
    BUTTON_STYLE_NORMAL,
    BUTTON_STYLE_RECORDING,
    BUTTON_STYLE_STOP,
    SCROLL_AREA_STYLE,
    STATUS_LABEL_STYLE,
    CHAT_CONTAINER_STYLE,
    BUTTON_TALK,
    STATUS_READY
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
    """Create a talk button widget.
    
    Returns:
        QPushButton: The configured talk button
    """
    button = QPushButton(BUTTON_TALK)
    button.setStyleSheet(BUTTON_STYLE_NORMAL)
    return button

def create_stop_button() -> QPushButton:
    """Create a stop button widget.
    
    Returns:
        QPushButton: The configured stop button
    """
    button = QPushButton()
    button.setIcon(QIcon("icons/stop2.png"))
    button.setIconSize(QSize(32, 32))
    button.setFixedSize(40, 40)
    button.setStyleSheet(BUTTON_STYLE_STOP)
    button.setVisible(False)
    return button

def create_text_input() -> QLineEdit:
    """Create a text input widget.
    
    Returns:
        QLineEdit: The configured text input
    """
    input_field = QLineEdit()
    input_field.setPlaceholderText("Type your message here...")
    return input_field

def create_send_button() -> QPushButton:
    """Create a send button widget.
    
    Returns:
        QPushButton: The configured send button
    """
    return QPushButton("Send")

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