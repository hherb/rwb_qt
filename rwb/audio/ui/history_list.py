"""Chat history list module.

This module provides a widget for displaying and selecting chat history files.
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QListWidget, 
    QListWidgetItem,
    QHBoxLayout,
    QPushButton
)
from PySide6.QtCore import Signal, Qt, QSize

class HistoryList(QWidget):
    """Widget for displaying and selecting chat history files.
    
    Signals:
        history_selected: Emitted when a history file is selected, with the file path
    """
    
    history_selected = Signal(str)  # Signal emitted when a history is selected
    
    def __init__(self, parent=None):
        """Initialize the history list widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.history_dir = Path.home() / ".rwb" / "chat_history"
        self.history_items: Dict[str, Path] = {}  # Maps display names to file paths
        
        self._setup_ui()
        self._load_histories()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Chat History")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 5px;
            }
            QListWidget::item {
                color: #ffffff;
                padding: 8px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
            }
            QListWidget::item:alternate {
                background-color: #333333;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._load_histories)
        layout.addWidget(refresh_button)
    
    def _load_histories(self) -> None:
        """Load chat history files and populate the list."""
        # Clear existing items
        self.list_widget.clear()
        self.history_items.clear()
        
        # Create history directory if it doesn't exist
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all JSON files in the history directory
        json_files = list(self.history_dir.glob("chat_*.json"))
        
        # Sort by modification time (newest first)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Add files to the list
        for file_path in json_files:
            display_name, conversation = self._get_history_info(file_path)
            self.history_items[display_name] = file_path
            
            # Create list item
            item = QListWidgetItem(display_name)
            
            # Set tooltip with conversation preview
            if conversation:
                tooltip = "\n".join([f"{msg['sender']}: {msg['text'][:50]}..." 
                                    for msg in conversation[:3]])
                if len(conversation) > 3:
                    tooltip += f"\n... ({len(conversation) - 3} more messages)"
                item.setToolTip(tooltip)
            
            self.list_widget.addItem(item)
    
    def _get_history_info(self, file_path: Path) -> Tuple[str, List]:
        """Get display name and conversation from a history file.
        
        Args:
            file_path: Path to the history file
            
        Returns:
            Tuple containing the display name and conversation data
        """
        # Extract date from filename
        filename = file_path.name
        conversation = []
        
        try:
            # Try to parse the timestamp from the filename
            # Format: chat_YYYYMMDD_HHMMSS.json
            date_str = filename[5:-5]  # Remove "chat_" and ".json"
            date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            date_display = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get message count and preview
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                message_count = len(conversation)
                
                # Create display name with date and message count
                display_name = f"{date_display} ({message_count} messages)"
                
            except (json.JSONDecodeError, IOError):
                # Fallback if we can't read the file
                display_name = f"{date_display} (error reading file)"
                
        except (ValueError, IndexError):
            # Fallback for filenames not matching the expected pattern
            display_name = filename
        
        return display_name, conversation
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click event.
        
        Args:
            item: The clicked list item
        """
        display_name = item.text()
        if display_name in self.history_items:
            file_path = self.history_items[display_name]
            self.history_selected.emit(str(file_path))
    
    def get_widget(self) -> QWidget:
        """Get the history list widget.
        
        Returns:
            QWidget: The history list widget
        """
        return self 