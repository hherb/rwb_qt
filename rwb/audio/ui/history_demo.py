"""Demo for the HistoryList widget.

This module provides a simple demo application for the HistoryList widget.
"""

import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QScrollArea,
    QPushButton,
    QHBoxLayout,
    QSplitter,
    QFrame
)
from PySide6.QtCore import Qt, Slot

from .history_list import HistoryList
from ..chat_message import ChatMessage, MessageSender

class HistoryDemo(QMainWindow):
    """Demo application for the HistoryList widget."""
    
    def __init__(self):
        """Initialize the demo application."""
        super().__init__()
        self.setWindowTitle("Chat History Demo")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)
        
        # Create left panel with history list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add history list widget
        self.history_list = HistoryList()
        self.history_list.history_selected.connect(self.on_history_selected)
        left_layout.addWidget(self.history_list, stretch=1)
        
        # Add to splitter
        splitter.addWidget(left_panel)
        
        # Create right panel for chat display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Add title
        chat_title = QLabel("Conversation")
        chat_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(chat_title)
        
        # Create chat scroll area similar to the main app
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #222222;
                border-radius: 10px;
                border: none;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_container.setStyleSheet("""
            QWidget {
                background-color: #222222;
            }
        """)
        
        self.chat_scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.chat_scroll, stretch=1)
        
        # Add info bar
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("color: #cccccc;")
        info_layout.addWidget(self.file_info_label)
        
        self.message_count_label = QLabel("")
        self.message_count_label.setStyleSheet("color: #cccccc;")
        info_layout.addWidget(self.message_count_label, alignment=Qt.AlignRight)
        
        right_layout.addWidget(info_frame)
        
        # Add to splitter
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
    
    def clear_chat(self):
        """Clear the chat display."""
        # Remove all widgets from the chat layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    @Slot(str)
    def on_history_selected(self, file_path: str):
        """Handle history selection.
        
        Args:
            file_path: Path to the selected history file
        """
        self.clear_chat()
        
        # Update info label
        path = Path(file_path)
        self.file_info_label.setText(f"File: {path.name}")
        
        # Try to load and display the file contents
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Display message count
            self.message_count_label.setText(f"{len(data)} messages")
            
            # Display the conversation using ChatMessage widgets
            for message in data:
                sender_str = message.get('sender', 'unknown')
                text = message.get('text', '')
                
                # Convert sender string to MessageSender enum
                if sender_str == 'user':
                    sender = MessageSender.USER
                elif sender_str == 'assistant':
                    sender = MessageSender.ASSISTANT
                elif sender_str == 'system':
                    sender = MessageSender.SYSTEM
                else:
                    sender = MessageSender.OTHER
                
                # Create and add chat message widget - the ChatMessage widget 
                # will properly render the markdown from the stored message
                chat_message = ChatMessage(text, sender)
                self.chat_layout.addWidget(chat_message)
            
            # Scroll to top
            self.chat_scroll.verticalScrollBar().setValue(0)
                
        except Exception as e:
            # Show error message in chat
            error_message = ChatMessage(f"Error loading file: {str(e)}", MessageSender.SYSTEM)
            self.chat_layout.addWidget(error_message)

def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    window = HistoryDemo()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 