"""Chat history list module.

This module provides a widget for displaying and selecting chat history files.
"""

import os
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
    QPushButton,
    QMenu,
    QToolButton,
    QMessageBox,
    QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QAction

class HistoryItemWidget(QWidget):
    """Custom widget for history list items with delete button."""
    
    delete_clicked = Signal(str)  # Signal emitted when delete button is clicked
    
    def __init__(self, display_name: str, file_path: str, parent=None):
        """Initialize the history item widget."""
        super().__init__(parent)
        self.file_path = file_path
        
        # Set widget styling to prevent border residues
        # self.setStyleSheet("""
        #     QWidget {
        #         background-color: transparent;
        #         border: none;
        #     }
        # """)
        
        # Create layout with appropriate padding
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(10)
        
        # Split the display name into timestamp and preview
        parts = display_name.split('\n', 1)
        title = parts[0]
        preview = parts[1] if len(parts) > 1 else ""
        
        # Create vertical layout for text
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        # Create title label with bold styling
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        text_layout.addWidget(self.title_label)
        
        # Create preview label with lighter styling if available
        if preview:
            self.preview_label = QLabel(preview)
            self.preview_label.setStyleSheet("font-size: 12px;")
            self.preview_label.setWordWrap(True)
            self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            text_layout.addWidget(self.preview_label)
        else:
            self.preview_label = None
        
        # Add text layout to main layout
        layout.addLayout(text_layout, 1)
        
        # Create delete button
        self.delete_button = QToolButton()
        self.delete_button.setIcon(self._get_trash_icon())
        self.delete_button.setIconSize(QSize(18, 18))
        self.delete_button.setFixedSize(QSize(28, 28))
        self.delete_button.setToolTip("Delete this history")
        self.delete_button.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #444;
                border-radius: 14px;
            }
        """)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self.delete_button, 0, Qt.AlignCenter)
    
    def _get_trash_icon(self):
        """Create a trash icon."""
        return QIcon.fromTheme("edit-delete", QIcon.fromTheme("trash-empty"))
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_clicked.emit(self.file_path)
    
    def get_file_path(self) -> str:
        """Get the file path associated with this item."""
        return self.file_path
    
    def get_display_name(self) -> str:
        """Get the display name."""
        return self.title_label.text()

class HistoryList(QWidget):
    """Widget for displaying and selecting chat history files.
    
    Signals:
        history_selected: Emitted when a history file is selected, with the file path
        history_deleted: Emitted when a history file is deleted
    """
    
    history_selected = Signal(str)  # Signal emitted when a history is selected
    history_deleted = Signal(str)   # Signal emitted when a history is deleted
    
    def __init__(self, parent=None):
        """Initialize the history list widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.history_dir = Path.home() / ".rwb" / "chat_history"
        self.history_items: Dict[str, Path] = {}  # Maps display names to file paths
        self.item_widgets: Dict[str, HistoryItemWidget] = {}  # Maps file paths to widgets
        
        self._setup_ui()
        self._load_histories()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Get font metrics for text-based sizing
        font_metrics = self.fontMetrics()
        line_height = font_metrics.height()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(line_height*0.7, line_height*0.7, line_height*0.7, line_height*0.7)
        layout.setSpacing(line_height/2)
        
        # Header
        header = QLabel("Chat History")
        header.setStyleSheet(f"font-size: {int(line_height * 1.4)}px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        
        # Calculate padding based on line height
        item_padding = int(line_height * 0.5)
        item_margin = int(line_height * 0.25)
        border_radius = int(line_height * 0.4)
        
        # Change the setup_ui function to adjust item selection behavior
        self.list_widget.setSelectionBehavior(QListWidget.SelectItems)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setItemAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Use calculated values in the stylesheet
        # self.list_widget.setStyleSheet(f"""
        #     QListWidget {{
        #         background-color: #292929;
        #         border-radius: {border_radius}px;
        #         padding: {int(line_height*0.3)}px;
        #         border: 1px solid #3a3a3a;
        #         outline: none;
        #         selection-background-color: transparent;
        #         show-decoration-selected: 0;
        #         alternate-background-color: #313131;
        #     }}
        #     QListWidget::item {{
        #         color: #ffffff;
        #         padding: {item_padding}px;
        #         border-radius: {border_radius}px;
        #         margin: {item_margin}px 0px;
        #         border: none;
        #         outline: none;
        #     }}
        #     QListWidget::item:selected {{
        #         background-color: #3d3d3d;
        #         border-left: 3px solid #4CAF50;
        #         border-top: none;
        #         border-right: none;
        #         border-bottom: none;
        #         outline: none;
        #     }}
        #     QListWidget::item:alternate {{
        #         background-color: #313131;
        #     }}
        #     QListWidget::item:hover {{
        #         background-color: #363636;
        #     }}
        #     /* Remove separator lines */
        #     QListView::separator {{
        #         height: 0px;
        #         background: transparent;
        #     }}
            
        #     /* Make sure no focus outline appears */
        #     *:focus {{
        #         outline: none;
        #     }}
        # """)
        
        # Configure list widget behavior
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)  # Smooth scrolling
        self.list_widget.setSpacing(item_margin)  # Spacing based on line height
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        # Add to layout with stretch factor
        layout.addWidget(self.list_widget, 1)  # Stretch to fill available space
        
        # Refresh button with modern styling
        refresh_button = QPushButton("Refresh")
        refresh_button.setMinimumHeight(int(line_height * 2))  # Button height based on line height
        # refresh_button.setStyleSheet(f"""
        #     QPushButton {{
        #         background-color: #3a3a3a;
        #         border-radius: {int(line_height * 0.3)}px;
        #         padding: {int(line_height * 0.3)}px;
        #         color: white;
        #         font-weight: bold;
        #     }}
        #     QPushButton:hover {{
        #         background-color: #4a4a4a;
        #     }}
        #     QPushButton:pressed {{
        #         background-color: #2a2a2a;
        #     }}
        # """)
        refresh_button.clicked.connect(self._load_histories)
        layout.addWidget(refresh_button)
    
    def _load_histories(self) -> None:
        """Load chat history files and populate the list."""
        # Clear existing items
        self.list_widget.clear()
        self.history_items.clear()
        self.item_widgets.clear()
        
        # Additional styling to remove frame focus
        self.list_widget.setFrameShape(QListWidget.NoFrame)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        
        # Create history directory if it doesn't exist
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all JSON files in the history directory
        json_files = list(self.history_dir.glob("chat_*.json"))
        
        # Sort by modification time (newest first)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Add files to the list
        for idx, file_path in enumerate(json_files):
            display_name, conversation = self._get_history_info(file_path)
            self.history_items[display_name] = file_path
            
            # Create list item with styling to remove bright residues
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            
            # Create and set custom widget
            item_widget = HistoryItemWidget(display_name, str(file_path))
            item_widget.delete_clicked.connect(self._delete_history)
            self.item_widgets[str(file_path)] = item_widget
            
            # Set fixed height for more consistent layout
            item.setSizeHint(QSize(self.list_widget.width(), 70))
            
            # Apply additional styling to prevent bright borders/residues
            item.setBackground(Qt.transparent)
            item.setForeground(Qt.transparent)
            
            # Create custom item style to avoid bright residues
            # Use alternating background colors based on index
            # custom_style = f"""
            #     background-color: {'#313131' if idx % 2 == 1 else '#292929'};
            #     border: none;
            #     outline: none;
            # """
            # item_widget.setStyleSheet(f"QWidget {{ {custom_style} }}")
            
            # Set the widget
            self.list_widget.setItemWidget(item, item_widget)
            
            # Set tooltip with conversation preview
            if conversation:
                tooltip = "\n".join([f"{msg['sender']}: {msg['text'][:50]}..." 
                                    for msg in conversation[:3]])
                if len(conversation) > 3:
                    tooltip += f"\n... ({len(conversation) - 3} more messages)"
                
                if hasattr(item_widget, 'preview_label') and item_widget.preview_label:
                    item_widget.preview_label.setToolTip(tooltip)
    
    def _get_history_info(self, file_path: Path) -> Tuple[str, List]:
        """Get display name and conversation from a history file."""
        # Extract date from filename
        filename = file_path.name
        conversation = []
        
        try:
            # Try to parse the timestamp from the filename
            # Format: chat_YYYYMMDD_HHMMSS.json
            date_str = filename[5:-5]  # Remove "chat_" and ".json"
            date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            
            # Format date to match the screenshot format: YYYY-MM-DD HH:MM (Z)
            date_display = date_obj.strftime("%Y-%m-%d %H:%M (%Z)")
            
            # Get message count and preview
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                message_count = len(conversation)
                
                # Create simple display name
                display_name = f"{date_display}"
                if message_count > 0:
                    display_name += f" ({message_count})"
                
                # Find first non-empty message
                preview_msg = ""
                if conversation:
                    for msg in conversation:
                        if msg.get("text", "").strip():
                            # Check sender type
                            sender = msg.get("sender", "")
                            # Add sender prefix to preview
                            if sender:
                                prefix = sender.capitalize() + ": "
                            else:
                                prefix = ""
                            preview_msg = prefix + msg.get("text", "").strip()
                            break
                
                # Add a short preview if available
                if preview_msg:
                    # Clean up text
                    preview_msg = " ".join(preview_msg.split())
                    # Keep preview short - slightly longer to match screenshot
                    if len(preview_msg) > 60:
                        preview_msg = preview_msg[:57] + "..."
                    # Add to display name
                    display_name += f"\n{preview_msg}"
                
            except (json.JSONDecodeError, IOError):
                # Fallback if we can't read the file
                display_name = f"{date_display} (error)"
                
        except (ValueError, IndexError):
            # Fallback for filenames not matching the expected pattern
            display_name = filename
        
        return display_name, conversation
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click event.
        
        Args:
            item: The clicked list item
        """
        # Get the custom widget from the item
        widget = self.list_widget.itemWidget(item)
        if widget and isinstance(widget, HistoryItemWidget):
            file_path = widget.get_file_path()
            
            # Update styling for selected item
            for i in range(self.list_widget.count()):
                list_item = self.list_widget.item(i)
                list_widget = self.list_widget.itemWidget(list_item)
                idx = i  # Get the item's index
                
                # if list_widget == widget:
                #     # Selected item
                #     list_widget.setStyleSheet("""
                #         QWidget {
                #             background-color: #3d3d3d;
                #             border-left: 3px solid #4CAF50;
                #             border-top: none;
                #             border-right: none;
                #             border-bottom: none;
                #             outline: none;
                #         }
                #     """)
                # else:
                #     # Not selected - use alternating colors
                #     custom_style = f"""
                #         background-color: {'#313131' if idx % 2 == 1 else '#292929'};
                #         border: none;
                #         outline: none;
                #     """
                #     list_widget.setStyleSheet(f"QWidget {{ {custom_style} }}")
            
            # Emit the signal
            self.history_selected.emit(file_path)
    
    def _delete_history(self, file_path: str) -> None:
        """Delete a history file after confirmation.
        
        Args:
            file_path: Path to the history file to delete
        """
        # Confirmation dialog
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Delete History")
        msg_box.setText("Are you sure you want to delete this chat history?")
        msg_box.setInformativeText("This action cannot be undone.")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        # Show dialog and handle response
        if msg_box.exec() == QMessageBox.Yes:
            try:
                # Delete the file
                os.remove(file_path)
                
                # Emit signal
                self.history_deleted.emit(file_path)
                
                # Reload the list
                self._load_histories()
            except Exception as e:
                # Show error message
                error_box = QMessageBox()
                error_box.setWindowTitle("Error")
                error_box.setText(f"Error deleting file: {str(e)}")
                error_box.setIcon(QMessageBox.Critical)
                error_box.exec()
    
    def get_widget(self) -> QWidget:
        """Get the history list widget.
        
        Returns:
            QWidget: The history list widget
        """
        return self 