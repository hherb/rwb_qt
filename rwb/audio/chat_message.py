"""Chat message widget module.

This module provides the ChatMessage widget for displaying messages
in the chat interface with proper styling and layout.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

class ChatMessage(QFrame):
    """A chat message widget with an icon and text."""
    
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("chatMessage")
        self.setStyleSheet(f"""
            QFrame#chatMessage {{
                background-color: {'#2d2d2d' if is_user else '#3d3d3d'};
                border-radius: 30px;
                padding: 10px;
                margin: 5px;
                margin-{'right' if is_user else 'left'}: 30px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Add icon
        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setText("👤" if is_user else "🤖")
        layout.addWidget(icon_label)
        
        # Add text
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: #ffffff;
            }
        """)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.text_edit)
        
        # Calculate initial size
        self.update_text(text)
        
    def update_text(self, text: str) -> None:
        """Update the message text and adjust height."""
        self.text_edit.setPlainText(text)
        
        # Force document update
        self.text_edit.document().adjustSize()
        
        # Get the document size
        doc = self.text_edit.document()
        doc_height = doc.size().height()
        
        # Calculate margins and padding
        margins = self.text_edit.contentsMargins()
        padding = 10  # Additional padding
        
        # Set the text edit height
        text_height = doc_height + margins.top() + margins.bottom() + padding
        self.text_edit.setFixedHeight(text_height)
        
        # Update the frame's minimum height
        frame_margins = self.contentsMargins()
        frame_height = text_height + frame_margins.top() + frame_margins.bottom()
        self.setMinimumHeight(frame_height)
        self.setMaximumHeight(frame_height) 