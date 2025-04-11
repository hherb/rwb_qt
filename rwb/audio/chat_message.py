"""Chat message widget module.

This module provides the ChatMessage widget for displaying messages
in the chat interface with proper styling and layout.
"""

from enum import Enum
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
import markdown

class MessageSender(Enum):
    """Enum for different types of message senders."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    OTHER = "other"

class ChatMessage(QFrame):
    """A chat message widget with an icon and text."""
    
    def __init__(self, text: str, sender: MessageSender, parent=None):
        super().__init__(parent)
        self.setObjectName("chatMessage")
        
        # Set style based on sender
        style_map = {
            MessageSender.USER: {
                "background": "#2d2d2d",
                "margin": "right",
                "icon": "👤"
            },
            MessageSender.ASSISTANT: {
                "background": "#3d3d3d",
                "margin": "left",
                "icon": "🤖"
            },
            MessageSender.SYSTEM: {
                "background": "#1d1d1d",
                "margin": "left",
                "icon": "⚙️"
            },
            MessageSender.OTHER: {
                "background": "#4d4d4d",
                "margin": "left",
                "icon": "❓"
            }
        }
        
        style = style_map[sender]
        self.setStyleSheet(f"""
            QFrame#chatMessage {{
                background-color: {style['background']};
                border-radius: 30px;
                padding: 10px;
                margin: 5px;
                margin-{style['margin']}: 30px;
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
        icon_label.setText(style['icon'])
        layout.addWidget(icon_label)
        
        # Add text
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(self._render_markdown(text))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: #ffffff;
            }
            a {
                color: #4CAF50;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            code {
                background-color: #2d2d2d;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }
            pre {
                background-color: #2d2d2d;
                padding: 10px;
                border-radius: 15px;
                margin: 10px 0;
            }
            blockquote {
                border-left: 4px solid #4CAF50;
                margin: 10px 0;
                padding-left: 15px;
                color: #cccccc;
            }
        """)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.text_edit)
        
        # Calculate initial size
        self.update_text(text)
        
    def _render_markdown(self, text: str) -> str:
        """Convert markdown text to HTML with custom styling."""
        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=['fenced_code', 'codehilite'])
        
        # Add custom styling
        return f"""
            <div style="color: #ffffff;">
                {html}
            </div>
        """
        
    def update_text(self, text: str) -> None:
        """Update the message text and adjust height."""
        self.text_edit.setHtml(self._render_markdown(text))
        
        # Force document update
        self.text_edit.document().adjustSize()
        
        # Get the document size
        doc = self.text_edit.document()
        doc_height = doc.size().height()
        
        # Calculate margins and padding
        margins = self.text_edit.contentsMargins()
        padding = 20  # Increased padding for better text display
        
        # Ensure minimum height for short messages
        min_text_height = self.text_edit.fontMetrics().height() * 2  # At least 2 lines of text height
        
        # Set the text edit height - ensure it's at least the minimum height
        text_height = max(min_text_height, doc_height) + margins.top() + margins.bottom() + padding
        self.text_edit.setFixedHeight(text_height)
        
        # Update the frame's minimum height
        frame_margins = self.contentsMargins()
        frame_padding = 20  # Additional frame padding
        frame_height = text_height + frame_margins.top() + frame_margins.bottom() + frame_padding
        self.setMinimumHeight(frame_height)
        self.setMaximumHeight(frame_height) 