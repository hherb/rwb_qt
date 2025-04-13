"""Audio assistant module.

This module provides the main GUI application for the voice assistant,
handling user interaction, audio recording, and displaying the conversation.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QSplitter, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QThread, Signal, Slot, QObject, QEvent, QSettings, QSize
from PySide6.QtGui import QIcon
from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions
from typing import Optional, Any, Dict

from rwb.agents.rwbagent import RWBAgent  # Updated import path

from .processor import AudioProcessor
from .chat_message import ChatMessage, MessageSender
from .chat_history import ChatHistory
from .recorder import AudioRecorder
from .ui.settings_dialog import SettingsDialog
from .ui.components import (
    create_status_label,
    create_talk_button,
    create_stop_button,
    create_text_input,
    create_send_button,
    create_chat_scroll_area,
    create_button_layout
)
from .ui.styles import (
    STATUS_READY,
    STATUS_LISTENING,
    STATUS_PROCESSING,
    STATUS_SPEAKING,
    STATUS_STOPPED,
    BUTTON_TALK,
    BUTTON_RECORDING,
    BUTTON_PROCESSING,
    BUTTON_STYLE_NORMAL,
    BUTTON_STYLE_RECORDING,
    SETTINGS_BUTTON_STYLE,
    TAB_WIDGET_STYLE,
    SPLITTER_STYLE
)
from .ui.history_list import HistoryList

class AudioAssistant(QMainWindow):
    """Main window for the voice assistant application."""
    
    def __init__(self) -> None:
        """Initialize the AudioAssistant."""
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize settings
        self.settings = QSettings("RWB", "VoiceAssistant")
        
        # Initialize chat history
        self.chat_history = ChatHistory()
        
        # Create UI components first (this will initialize self.chat_layout)
        self.setup_tabbed_ui()
        
        # Initialize the RWB agent for LLM inference
        # only after UI components are set up
        self.agent = RWBAgent()
        
        # Initialize audio recorder
        self.recorder = AudioRecorder()
        
        # Initialize models with settings
        self.stt_model = get_stt_model()
        self.tts_model = get_tts_model(model="kokoro")
        self.tts_options = KokoroTTSOptions(
            voice=self.settings.value("tts/voice", "bf_emma"),
            speed=1.0,
            lang="en-us"
        )
        
        # Initialize audio processor 
        self.processor = AudioProcessor(
            stt_model=self.stt_model,
            tts_model=self.tts_model,
            tts_options=self.tts_options
        )
        
        # Connect audio processor signals
        self.processor.speaking.connect(self.handle_speaking_started)
        self.processor.done_speaking.connect(self.handle_speaking_ended)
        self.processor.stt_completed.connect(self.handle_stt_completed)
        self.processor.error.connect(self.handle_processing_error)
        
        # Connect agent with audio processor
        self.agent.set_audio_processor(self.processor)
        
        # Connect agent signals to UI
        self.agent.feedback.connect(self.handle_feedback)
        self.agent.text_update.connect(self.handle_text_update)
        
        self.current_messages: Dict[str, ChatMessage] = {}
        self.current_message_id: str = ""  # Current session message ID
        self.attached_files: list[str] = []  # List to store attached file paths
    
    def setup_tabbed_ui(self) -> None:
        """Set up the tabbed user interface."""
        # Create central widget and tab container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout for the central widget
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a toolbar-like area at the top for settings button
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 0)
        
        # Create settings button with cogwheel icon
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon("rwb/icons/cogwheel.png"))
        self.settings_button.setIconSize(QSize(24, 24))
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setStyleSheet(SETTINGS_BUTTON_STYLE)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        
        # Add settings button to toolbar layout
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addStretch(1)  # Push settings button to the left
        
        # Add toolbar to main layout
        main_layout.addWidget(toolbar)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)  # Keep tabs at the top
        self.tab_widget.setStyleSheet(TAB_WIDGET_STYLE)
        
        # Create main chat tab
        self.chat_tab = QWidget()
        self.setup_chat_ui()
        self.tab_widget.addTab(self.chat_tab, "Chat")
        
        # Create history tab
        self.history_tab = QWidget()
        self.setup_history_ui()
        self.tab_widget.addTab(self.history_tab, "History")
        
        # Connect tab changes
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Add tabs to main layout
        main_layout.addWidget(self.tab_widget)
    
    def setup_chat_ui(self) -> None:
        """Set up the chat user interface."""
        # Create main layout for chat tab
        chat_layout = QVBoxLayout(self.chat_tab)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        chat_layout.setSpacing(20)
        
        # Create status label
        self.status_label = create_status_label()
        chat_layout.addWidget(self.status_label)
        
        # Create chat scroll area
        scroll_area, self.chat_container, self.chat_layout = create_chat_scroll_area()
        chat_layout.addWidget(scroll_area, stretch=1)
        
        # Create input area with buttons
        input_area = QWidget()
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # Create file attachment button with paperclip icon
        self.attach_button = QPushButton()
        self.attach_button.setIcon(QIcon("rwb/icons/paperclip.png"))
        self.attach_button.setIconSize(QSize(24, 24))
        self.attach_button.setToolTip("Attach files (images, PDFs, etc.)")
        self.attach_button.setFixedSize(40, 40)
        self.attach_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.attach_button.clicked.connect(self.open_file_dialog)
        input_layout.addWidget(self.attach_button)
        
        # Create text input
        self.text_input = create_text_input()
        self.text_input.textChanged.connect(self.on_text_changed)
        
        # Enable enter key for sending
        self.text_input.installEventFilter(self)
        
        input_layout.addWidget(self.text_input, stretch=1)
        
        # Create a container for right-side buttons
        right_buttons = QWidget()
        right_layout = QHBoxLayout(right_buttons)  # Changed to horizontal layout
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)  # Space between buttons
        
        # Create send button
        self.send_button = create_send_button()
        self.send_button.setFixedHeight(75)
        self.send_button.setVisible(False)
        self.send_button.clicked.connect(self.send_text)
        right_layout.addWidget(self.send_button)
        
        # Create talk button
        self.talk_button = create_talk_button()
        self.talk_button.setFixedSize(75, 75)  # Make it square
        self.talk_button.pressed.connect(self.start_recording)
        self.talk_button.released.connect(self.stop_recording)
        right_layout.addWidget(self.talk_button)
        
        # Create stop button
        self.stop_button = create_stop_button()
        self.stop_button.clicked.connect(self.stop_processing)
        right_layout.addWidget(self.stop_button)
        
        # Add right buttons to input layout
        input_layout.addWidget(right_buttons)
        
        # Add input area to main layout
        chat_layout.addWidget(input_area)
    
    def setup_history_ui(self) -> None:
        """Set up the history tab user interface."""
        # Create main layout for history tab
        history_layout = QVBoxLayout(self.history_tab)
        history_layout.setContentsMargins(20, 20, 20, 20)
        history_layout.setSpacing(20)
        
        # Create status label for history tab
        self.history_status_label = create_status_label()
        self.history_status_label.setText("Select a chat history to view")
        history_layout.addWidget(self.history_status_label)
        
        # Create splitter for horizontal layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent collapsing sections completely
        splitter.setStyleSheet(SPLITTER_STYLE)
        
        # Create history list widget (left side)
        self.history_list = HistoryList()
        self.history_list.history_selected.connect(self.on_history_selected)
        self.history_list.history_deleted.connect(self.on_history_deleted)
        
        # Create right side widget for chat display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Create chat display scroll area (right side)
        self.history_scroll, self.history_container, self.history_chat_layout = create_chat_scroll_area()
        right_layout.addWidget(self.history_scroll)
        
        # Add widgets to splitter
        splitter.addWidget(self.history_list)
        splitter.addWidget(right_widget)
        
        # Set initial sizes (40% for list, 60% for chat display)
        splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        history_layout.addWidget(splitter, 1)
    
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change events.
        
        Args:
            index: The index of the selected tab
        """
        if index == 1:  # History tab
            # Refresh history list when switching to this tab
            self.history_list._load_histories()
    
    def on_history_deleted(self, file_path: str) -> None:
        """Handle history deletion.
        
        Args:
            file_path: Path to the deleted history file
        """
        # Clear the chat layout if the currently viewed history was deleted
        self.clear_history_view()
        self.history_status_label.setText("History deleted. Select another chat history to view.")
    
    def clear_history_view(self) -> None:
        """Clear the history view."""
        while self.history_chat_layout.count():
            item = self.history_chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def on_history_selected(self, file_path: str) -> None:
        """Handle history selection.
        
        Args:
            file_path: Path to the selected history file
        """
        import json
        from pathlib import Path
        
        # Clear the chat layout
        self.clear_history_view()
        
        # Update status label
        path = Path(file_path)
        self.history_status_label.setText(f"Viewing: {path.name}")
        
        # Try to load and display the file contents
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
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
                
                # Create and add chat message widget
                chat_message = ChatMessage(text, sender)
                self.history_chat_layout.addWidget(chat_message)
            
            # Scroll to top
            self.history_scroll.verticalScrollBar().setValue(0)
                
        except Exception as e:
            # Show error message
            self.history_status_label.setText(f"Error loading file: {str(e)}")
    
    def start_recording(self) -> None:
        """Start recording audio."""
        if not self.recorder.recording:
            self.recorder.start_recording()
            self.talk_button.setIcon(QIcon("rwb/icons/sst_red.png"))
            self.status_label.setText(STATUS_LISTENING)
            # Hide the send button while recording
            if hasattr(self, 'send_button'):
                self.send_button.setVisible(False)
    
    def stop_recording(self) -> None:
        """Stop recording and start processing."""
        if self.recorder.recording:
            audio_data = self.recorder.stop_recording()
            
            self.status_label.setText(STATUS_PROCESSING)
            self.talk_button.setEnabled(False)
            self.talk_button.setIcon(QIcon("rwb/icons/sst_green.png"))  # Reset icon back to green
            self.stop_button.setVisible(True)
            
            # Create a unique message ID for this session
            self.current_message_id = str(id(self)) + "_" + str(id(audio_data))
            
            # Process audio directly with the agent
            self.agent.process_audio_input(audio_data, self.recorder.RATE)
    
    def stop_processing(self) -> None:
        """Stop any ongoing audio processing."""
        # Cancel any ongoing processing tasks
        if self.processor:
            self.processor.cancel_processing()
            
        # Update UI state
        self.status_label.setText(STATUS_STOPPED)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.talk_button.setStyleSheet(BUTTON_STYLE_NORMAL)
        
        # Reset cancellation flag for future tasks
        if self.processor:
            self.processor.reset_cancellation_flag()
    
    @Slot(str, str)
    def handle_text_update(self, message_id: str, text: str) -> None:
        """Handle text updates from the audio processor."""
        if message_id not in self.current_messages:
            # Create new message if it doesn't exist
            is_user = message_id.endswith("_user")
            sender = MessageSender.USER if is_user else MessageSender.ASSISTANT
            message = ChatMessage(text, sender)
            self.chat_layout.addWidget(message)
            self.current_messages[message_id] = message
            
            # Add user messages to chat history immediately (they're complete)
            if is_user and text.strip():
                self.chat_history.add_message(text, sender, message_id)
                self.chat_history.complete_message(message_id)
                self.chat_history.save()
        else:
            # Update existing message UI only, don't update chat history for assistant messages
            self.current_messages[message_id].update_text(text)
        
        # Scroll to bottom
        scroll_area = self.chat_container.parent().parent()
        scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().maximum()
        )
    
    @Slot(str, str)
    def handle_processing_finished(self, user_text: str, assistant_text: str) -> None:
        """Handle completion of audio processing."""
        # Determine assistant message ID
        if hasattr(self.processor, 'current_message_id') and self.processor.current_message_id:
            # Use processor's message ID if available
            assistant_id = f"{self.processor.current_message_id}_assistant"
        elif self.current_message_id:
            # Use our own message ID if available
            assistant_id = f"{self.current_message_id}_assistant"
        else:
            # Fallback to a new ID
            assistant_id = f"{id(self)}_assistant"
            
        if assistant_id in self.current_messages:
            # Use the assistant_text directly from the processor response,
            # which is the original markdown, rather than extracting from the UI widget
            # which would give us the HTML rendered version
            
            final_text = assistant_text if assistant_text.strip() else ""
            
            # Only process if there's actual text
            if final_text.strip():
                # Add the original markdown text to chat history
                self.chat_history.add_message(final_text, MessageSender.ASSISTANT, assistant_id)
                self.chat_history.complete_message(assistant_id)
                self.chat_history.save()
        else:
            # If assistant message wasn't found, create it directly
            if assistant_text.strip():
                self.chat_history.add_message(assistant_text, MessageSender.ASSISTANT, assistant_id)
                self.chat_history.complete_message(assistant_id)
                self.chat_history.save()
        
        # Reset UI state
        self.status_label.setText(STATUS_READY)
        self.talk_button.setStyleSheet(BUTTON_STYLE_NORMAL)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)
    
    @Slot(str)
    def handle_processing_error(self, error_message: str) -> None:
        """Handle errors during audio processing."""
        self.status_label.setText(f"Error: {error_message}")
        self.handle_processing_ended()
    
    @Slot()
    def handle_speaking_started(self) -> None:
        """Handle the start of speech synthesis."""
        self.status_label.setText(STATUS_SPEAKING)
    
    @Slot()
    def handle_speaking_ended(self) -> None:
        """Handle the end of speech synthesis."""
        self.handle_processing_ended()
    
    def handle_processing_ended(self) -> None:
        """Handle the end of processing."""
        self.status_label.setText(STATUS_READY)
        self.talk_button.setStyleSheet(BUTTON_STYLE_NORMAL)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)
    
    def on_text_changed(self) -> None:
        """Handle text changes in the text input field."""
        # Add a Send button if there's text, otherwise hide it
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        
        text = self.text_input.toPlainText().strip()
        if hasattr(self, 'send_button'):
            self.send_button.setVisible(bool(text))
    
    def open_file_dialog(self) -> None:
        """Open a file dialog to select files for context."""
        from PySide6.QtWidgets import QFileDialog
        
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Supported files (*.png *.jpg *.jpeg *.pdf *.txt *.docx *.md);;All files (*)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.process_selected_files(selected_files)
    
    def process_selected_files(self, file_paths: list[str]) -> None:
        """Process the selected files for context.
        
        Args:
            file_paths: List of selected file paths
        """
        # Add system message about attached files
        file_names = [f.split("/")[-1] for f in file_paths]
        message_text = f"📎 Files attached: {', '.join(file_names)}"
        
        # Create system message
        system_message = ChatMessage(message_text, MessageSender.SYSTEM)
        self.chat_layout.addWidget(system_message)
        
        # Store file paths for processing with the next user message
        self.attached_files = file_paths
        
        # Log attachment
        print(f"Attached files: {file_paths}")
        
        # TODO: Add functionality to actually process these files when sending a message 


    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter events for text input to handle key presses.
        
        Args:
            obj: The object the event was sent to
            event: The event
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        from PySide6.QtCore import QEvent, Qt
        
        if obj is self.text_input and event.type() == QEvent.KeyPress:
            key_event = event
            # Ctrl+Enter to send message
            if (key_event.key() == Qt.Key_Return or key_event.key() == Qt.Key_Enter) and key_event.modifiers() == Qt.ControlModifier:
                self.send_text()
                return True
        return super().eventFilter(obj, event)
        
    def send_text(self) -> None:
        """Handle text input from the text input field."""
        text = self.text_input.toPlainText().strip()
        if text:
            # Clear the input field
            self.text_input.clear()
            self.send_button.setVisible(False)
            
            # Create a unique message ID for this session
            self.current_message_id = str(id(self))
            
            # Manually add user message to display and chat history
            user_message_id = f"{self.current_message_id}_user"
            user_sender = MessageSender.USER
            user_message = ChatMessage(text, user_sender)
            self.chat_layout.addWidget(user_message)
            self.current_messages[user_message_id] = user_message
            
            # Add user message to chat history
            self.chat_history.add_message(text, user_sender, user_message_id)
            self.chat_history.complete_message(user_message_id)
            
            # Process attached files if any
            if self.attached_files:
                # TODO: Implement proper file processing
                print(f"Processing attached files with message: {self.attached_files}")
                # Clear the list after processing
                self.attached_files = []
            
            # Process text input with the agent
            self.agent.process_user_input(text)
            
            # Update UI state
            self.talk_button.setEnabled(False)
            self.stop_button.setVisible(True)
            self.status_label.setText(STATUS_PROCESSING)
    
    def closeEvent(self, event: Any) -> None:
        """Handle window close event."""
        if self.recorder.recording:
            self.recorder.stop_recording()
        
        # Clean up audio processor resources
        if self.processor:
            self.processor.close()
        
        # Save chat history before closing
        self.chat_history.save()
        
        # Clean up audio resources
        self.recorder.cleanup()
        event.accept()
    
    @Slot(str, str)
    def handle_feedback(self, message: str, message_type: str) -> None:
        """Handle feedback messages from the agent or processor.
        
        Args:
            message: The message to display
            message_type: Type of message (info, debug, error)
        """
        # Only display debug messages if we're in debug mode
        if message_type == "debug":
            # Skip debug messages in the UI for now
            # Could add a setting to enable/disable debug messages
            return
        
        # Format the message based on type
        if message_type == "error":
            formatted_message = f"⚠️ {message}"
        elif message_type == "info":
            formatted_message = f"ℹ️ {message}"
        else:
            formatted_message = message
        
        # Create system message in chat UI
        system_message = ChatMessage(formatted_message, MessageSender.SYSTEM)
        self.chat_layout.addWidget(system_message)
        
        # Save system message to chat history
        system_message_id = f"{id(message)}_{message_type}_system"
        self.chat_history.add_message(formatted_message, MessageSender.SYSTEM, system_message_id)
        self.chat_history.complete_message(system_message_id)
        self.chat_history.save()
        
        # Scroll to show the message
        scroll_area = self.chat_container.parent().parent()
        scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().maximum()
        )
    
    def open_settings_dialog(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings that might have changed
            self.tts_options.voice = self.settings.value("tts/voice", "bf_emma")
            
            # Update the model name if needed
            model_name = self.settings.value("model/name", "")
            if model_name and hasattr(self, 'agent'):
                # Update the agent's model name if possible
                # This might need to be implemented in the RWBAgent class
                try:
                    self.agent.set_model_name(model_name)
                except AttributeError:
                    # If the agent doesn't have this method, just log it
                    print(f"Note: Agent doesn't support changing model name to {model_name}")
    
    @Slot(str)
    def handle_stt_completed(self, text: str) -> None:
        """Handle completion of speech-to-text conversion.
        
        Args:
            text: The transcribed text
        """
        # Don't do anything here as the agent's process_audio_input method
        # already handles adding the text to the UI
        pass