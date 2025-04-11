"""Audio assistant module.

This module provides the main GUI application for the voice assistant,
handling user interaction, audio recording, and displaying the conversation.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QThread, Signal, Slot
from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions
from typing import Optional, Any, Dict

from .processor import AudioProcessor
from .chat_message import ChatMessage, MessageSender
from .chat_history import ChatHistory
from .recorder import AudioRecorder
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
    BUTTON_STYLE_RECORDING
)

class AudioAssistant(QMainWindow):
    """Main window for the voice assistant application."""
    
    def __init__(self) -> None:
        """Initialize the AudioAssistant."""
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize chat history
        self.chat_history = ChatHistory()
        
        # Initialize audio recorder
        self.recorder = AudioRecorder()
        
        # Initialize models
        self.stt_model = get_stt_model()
        self.tts_model = get_tts_model(model="kokoro")
        self.tts_options = KokoroTTSOptions(
            voice="bf_emma",
            speed=1.0,
            lang="en-us"
        )
        
        self.processor: Optional[AudioProcessor] = None
        self.current_messages: Dict[str, ChatMessage] = {}
        self.current_message_id: str = ""  # Current session message ID
        
        # Create UI
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create status label
        self.status_label = create_status_label()
        main_layout.addWidget(self.status_label)
        
        # Create chat scroll area
        scroll_area, self.chat_container, self.chat_layout = create_chat_scroll_area()
        main_layout.addWidget(scroll_area, stretch=1)
        
        # Create button container
        button_container = QWidget()
        main_layout.addWidget(button_container)
        
        # Create button layout
        button_layout = create_button_layout(button_container)
        
        # Create buttons
        self.talk_button = create_talk_button()
        self.talk_button.pressed.connect(self.start_recording)
        self.talk_button.released.connect(self.stop_recording)
        button_layout.addWidget(self.talk_button)
        
        self.stop_button = create_stop_button()
        self.stop_button.clicked.connect(self.stop_processing)
        button_layout.addWidget(self.stop_button)
        
        # Create text input
        self.text_input = create_text_input()
        self.text_input.returnPressed.connect(self.send_text)
        main_layout.addWidget(self.text_input)
        
        # Create send button
        self.send_button = create_send_button()
        self.send_button.clicked.connect(self.send_text)
        main_layout.addWidget(self.send_button)
    
    def start_recording(self) -> None:
        """Start recording audio."""
        if not self.recorder.recording:
            self.recorder.start_recording()
            self.talk_button.setText(BUTTON_RECORDING)
            self.talk_button.setStyleSheet(BUTTON_STYLE_RECORDING)
            self.status_label.setText(STATUS_LISTENING)
    
    def stop_recording(self) -> None:
        """Stop recording and start processing."""
        if self.recorder.recording:
            audio_data = self.recorder.stop_recording()
            
            self.talk_button.setText(BUTTON_PROCESSING)
            self.status_label.setText(STATUS_PROCESSING)
            self.talk_button.setEnabled(False)
            self.stop_button.setVisible(True)
            
            # Create a unique message ID for this session
            self.current_message_id = str(id(self)) + "_" + str(id(audio_data))
            
            # Start the audio processor thread
            self.processor = AudioProcessor(
                audio_data=audio_data,
                sample_rate=self.recorder.RATE,
                stt_model=self.stt_model,
                tts_model=self.tts_model,
                tts_options=self.tts_options
            )
            
            # Connect signals
            self.processor.finished.connect(self.handle_processing_finished)
            self.processor.error.connect(self.handle_processing_error)
            self.processor.speaking.connect(self.handle_speaking_started)
            self.processor.done_speaking.connect(self.handle_speaking_ended)
            self.processor.text_update.connect(self.handle_text_update)
            
            # Start the processor
            self.processor.start()
    
    def stop_processing(self) -> None:
        """Stop any ongoing audio processing."""
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
            self.processor = None
            self.status_label.setText(STATUS_STOPPED)
            self.talk_button.setEnabled(True)
            self.stop_button.setVisible(False)
            self.talk_button.setText(BUTTON_TALK)
            self.talk_button.setStyleSheet(BUTTON_STYLE_NORMAL)
    
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
                print(f"Adding user message to history: {text}")
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
            # Get the final text from the current message widget
            final_text = self.current_messages[assistant_id].text_edit.toPlainText()
            
            # Only process if there's actual text
            if final_text.strip():
                print(f"Adding assistant message to history: {final_text[:30]}...")
                # Only now add the complete assistant message to chat history
                self.chat_history.add_message(final_text, MessageSender.ASSISTANT, assistant_id)
                self.chat_history.complete_message(assistant_id)
                self.chat_history.save()
                print(f"Saved chat history to {self.chat_history.current_session_filename}")
        else:
            # If assistant message wasn't found, create it directly
            if assistant_text.strip():
                print(f"Directly adding assistant message to history (message not found in UI)")
                self.chat_history.add_message(assistant_text, MessageSender.ASSISTANT, assistant_id)
                self.chat_history.complete_message(assistant_id)
                self.chat_history.save()
        
        # Reset UI state
        self.status_label.setText(STATUS_READY)
        self.talk_button.setText(BUTTON_TALK)
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
        self.talk_button.setText(BUTTON_TALK)
        self.talk_button.setStyleSheet(BUTTON_STYLE_NORMAL)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)
    
    def send_text(self) -> None:
        """Handle text input from the text input field."""
        text = self.text_input.text().strip()
        if text:
            # Clear the input field
            self.text_input.clear()
            
            # Create a unique message ID for this session
            self.current_message_id = str(id(self))
            
            # Start the audio processor with the text
            self.processor = AudioProcessor(
                audio_data=None,
                sample_rate=self.recorder.RATE,
                stt_model=self.stt_model,
                tts_model=self.tts_model,
                tts_options=self.tts_options
            )
            
            # Connect signals
            self.processor.finished.connect(self.handle_processing_finished)
            self.processor.error.connect(self.handle_processing_error)
            self.processor.speaking.connect(self.handle_speaking_started)
            self.processor.done_speaking.connect(self.handle_speaking_ended)
            self.processor.text_update.connect(self.handle_text_update)
            
            # Manually add user message to display and chat history
            user_message_id = f"{self.current_message_id}_user"
            user_sender = MessageSender.USER
            user_message = ChatMessage(text, user_sender)
            self.chat_layout.addWidget(user_message)
            self.current_messages[user_message_id] = user_message
            
            # Add user message to chat history
            self.chat_history.add_message(text, user_sender, user_message_id)
            self.chat_history.complete_message(user_message_id)
            
            # Start the processor with text input
            self.processor.start(text)
            
            # Update UI state
            self.talk_button.setEnabled(False)
            self.stop_button.setVisible(True)
            self.status_label.setText(STATUS_PROCESSING)
    
    def closeEvent(self, event: Any) -> None:
        """Handle window close event."""
        if self.recorder.recording:
            self.recorder.stop_recording()
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
        
        # Save chat history before closing
        self.chat_history.save()
        
        # Clean up audio resources
        self.recorder.cleanup()
        event.accept() 