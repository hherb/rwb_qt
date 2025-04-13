"""Chat message widget module.

This module provides the ChatMessage widget for displaying messages
in the chat interface with proper styling and layout.
"""

from enum import Enum
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QPixmap
import markdown
import os
from .ui.styles import MESSAGE_USER_STYLE, MESSAGE_SYSTEM_STYLE, ICON_LABEL_STYLE

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
                "icon": "horstcartoon.png"
            },
            MessageSender.ASSISTANT: {
                "background": "#3d3d3d",
                "margin": "left",
                "icon": "ollama_transparent.png",
                "icon_background": "#add8e6"  # Light blue background
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
        
        # Check if it's an image file or emoji
        if style['icon'].endswith(('.png', '.jpg', '.jpeg')):
            # Get the path to the icons directory - correctly navigate to the rwb/icons directory
            # Go up from audio to rwb folder, then find icons subfolder
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons')
            icon_path = os.path.join(icons_dir, style['icon'])
            # Check if the icon file exists            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                # Scale the image to fit while maintaining aspect ratio
                pixmap = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Apply background if specified in the style
                if 'icon_background' in style:
                    bg_color = style['icon_background']
                    # Create a style with circular background
                    icon_label.setStyleSheet(f"""
                        background-color: {bg_color}; 
                        border-radius: 20px;
                        padding: 2px;
                    """)
                
                icon_label.setPixmap(pixmap)
            else:
                print(f"Icon not found at: {icon_path}")
                # Fallback if image not found
                icon_label.setStyleSheet(ICON_LABEL_STYLE)
                icon_label.setText("👤")
        else:
            # For emoji icons
            icon_label.setStyleSheet(ICON_LABEL_STYLE)
            icon_label.setText(style['icon'])
            
        layout.addWidget(icon_label)
        
        # Add text
        # Use QTextBrowser instead of QTextEdit for link handling capability
        from PySide6.QtWidgets import QTextBrowser
        self.text_edit = QTextBrowser()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(self._render_markdown(text))
        # Set up proper link handling
        self.text_edit.setOpenExternalLinks(False)  # Don't open links automatically
        self.text_edit.setOpenLinks(False)  # Prevent internal navigation
        self.text_edit.anchorClicked.connect(self._open_external_link)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: #ffffff;
            }
            a {
                color: #00BFFF;  /* Much brighter blue (DeepSkyBlue) for better contrast */
                text-decoration: underline;
                font-weight: bold;
            }
            a:hover {
                color: #00FFFF;  /* Cyan on hover - even brighter */
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
        
        # Replace links with links that have title attributes for tooltips
        # This simple regex replacement adds the URL as a title attribute to show on hover
        import re
        html = re.sub(r'<a href="([^"]+)"([^>]*)>',
                     r'<a href="\1" title="\1"\2>',
                     html)
        
        # Add custom styling
        return f"""
            <div style="color: #ffffff;">
                {html}
            </div>
        """
    
    def _open_external_link(self, url):
        """Open links in the system's default web browser."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))
        
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
        padding = 8  # Reduced padding for more compact display
        
        # Ensure minimum height for short messages
        min_text_height = self.text_edit.fontMetrics().height() * 1.5  # Reduced from 2 lines to 1.5
        
        # Set the text edit height - ensure it's at least the minimum height
        text_height = max(min_text_height, doc_height) + margins.top() + margins.bottom() + padding
        self.text_edit.setFixedHeight(text_height)
        
        # Update the frame's minimum height with minimal padding
        frame_margins = self.contentsMargins()
        # Reduced padding to half a line height
        frame_padding = self.text_edit.fontMetrics().height() * 0.5
        frame_height = text_height + frame_margins.top() + frame_margins.bottom() + frame_padding
        self.setMinimumHeight(frame_height)
        self.setMaximumHeight(frame_height)