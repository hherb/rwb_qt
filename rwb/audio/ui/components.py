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
    """Create a talk button widget with a microphone icon.
    
    Returns:
        QPushButton: The configured talk button with microphone icon
    """
    button = QPushButton()
    
    # Create a microphone icon container
    layout = QVBoxLayout(button)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Create a microphone icon widget
    mic_container = QWidget()
    mic_container.setFixedSize(30, 30)
    mic_container_layout = QVBoxLayout(mic_container)
    mic_container_layout.setContentsMargins(0, 0, 0, 0)
    
    # Create the microphone body
    mic_body = QFrame(mic_container)
    mic_body.setFixedSize(16, 22)
    mic_body.setStyleSheet("""
        background-color: white;
        border-radius: 4px;
    """)
    
    # Create the microphone base
    mic_base = QFrame(mic_container)
    mic_base.setFixedSize(20, 6)
    mic_base.setStyleSheet("""
        background-color: white;
        border-radius: 3px;
    """)
    
    # Position the parts
    mic_container_layout.addWidget(mic_body, alignment=Qt.AlignHCenter | Qt.AlignTop)
    mic_container_layout.addWidget(mic_base, alignment=Qt.AlignHCenter | Qt.AlignBottom)
    
    layout.addWidget(mic_container, alignment=Qt.AlignCenter)
    
    button.setStyleSheet(BUTTON_STYLE_NORMAL)
    return button

def create_stop_button() -> QPushButton:
    """Create a stop button widget.
    
    Returns:
        QPushButton: The configured stop button
    """
    button = QPushButton()
    # Create a custom stop icon with gray background and red square
    button.setStyleSheet("""
        QPushButton {
            background-color: #707070;
            border-radius: 20px;
            min-width: 40px;
            min-height: 40px;
        }
        QPushButton:hover {
            background-color: #808080;
        }
        QPushButton::pressed {
            background-color: #606060;
        }
        QPushButton:disabled {
            background-color: #505050;
        }
    """)
    
    # Add a red square in the center
    layout = QVBoxLayout(button)
    layout.setContentsMargins(12, 12, 12, 12)  # Create margin for the square inside the circle
    
    stop_square = QFrame()
    stop_square.setFixedSize(16, 16)
    stop_square.setFrameShape(QFrame.StyledPanel)
    stop_square.setStyleSheet("background-color: #d32f2f;")  # Red color
    
    layout.addWidget(stop_square)
    layout.setAlignment(Qt.AlignCenter)
    
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