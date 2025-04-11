"""Audio assistant module.

This module provides the main GUI application for the voice assistant,
handling user interaction, audio recording, and displaying the conversation.
"""

import sys
import numpy as np
import pyaudio
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QTextEdit,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot, QSize
from PySide6.QtGui import QFont, QTextCursor, QIcon
from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions
from typing import Optional, Any, Dict
import os
import json
from datetime import datetime
from pathlib import Path

from .processor import AudioProcessor
from .chat_message import ChatMessage
from .chat_history import ChatHistory

class AudioAssistant(QMainWindow):
    """Main window for the voice assistant application.
    
    This class provides the GUI interface for the voice assistant,
    including audio recording controls and conversation display.
    
    Attributes:
        CHUNK (int): Size of audio chunks for recording
        FORMAT (int): Audio format (32-bit float)
        CHANNELS (int): Number of audio channels
        RATE (int): Audio sample rate
        KOKORO_RATE (int): Sample rate used by the TTS model
        recording (bool): Whether currently recording
        frames (list): List of recorded audio frames
        processor (Optional[AudioProcessor]): Current audio processor instance
        current_messages (Dict[str, ChatMessage]): Dictionary to keep track of current messages
    """
    
    def __init__(self) -> None:
        """Initialize the AudioAssistant.
        
        Sets up the window, audio parameters, and initializes the UI.
        """
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize chat history
        self.chat_history = ChatHistory()
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100  # PyAudio output rate
        self.KOKORO_RATE = 24000  # Kokoro's native rate
        self.recording = False
        self.frames = []
        self.processor: Optional[AudioProcessor] = None
        self.current_messages: Dict[str, ChatMessage] = {}
        
        # Initialize models
        self.stt_model = get_stt_model()
        self.tts_model = get_tts_model(model="kokoro")
        self.tts_options = KokoroTTSOptions(
            voice="bf_emma",
            speed=1.0,
            lang="en-us"
        )
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
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
        self.status_label = QLabel("Ready to talk")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Create scroll area for chat messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3d3d3d;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create container for chat messages
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_container.setStyleSheet("background-color: #1e1e1e;")
        scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(scroll_area, stretch=1)
        
        # Create button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Create buttons
        self.talk_button = QPushButton("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
            }
        """)
        self.talk_button.pressed.connect(self.start_recording)
        self.talk_button.released.connect(self.stop_recording)
        button_layout.addWidget(self.talk_button)
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(QIcon("icons/stop2.png"))
        self.stop_button.setIconSize(QSize(32, 32))
        self.stop_button.setFixedSize(40, 40)  # Slightly larger than icon for better visibility
        self.stop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                border-radius: 20px;
                padding: 4px;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setVisible(False)  # Initially hidden
        button_layout.addWidget(self.stop_button)
        
        # Create text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.returnPressed.connect(self.send_text)
        main_layout.addWidget(self.text_input)
        
        # Create send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_text)
        main_layout.addWidget(self.send_button)
    
    def add_message(self, text: str, is_user: bool):
        """Add a new message to the chat."""
        message = ChatMessage(text, is_user)
        self.chat_layout.addWidget(message)
        # Scroll to bottom
        scroll_area = self.chat_container.parent().parent()
        scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().maximum()
        )
    
    def stop_processing(self) -> None:
        """Stop any ongoing audio processing.
        
        Terminates the current audio processor thread and resets the UI state.
        """
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
            self.processor = None
            self.status_label.setText("Processing stopped")
            self.talk_button.setEnabled(True)
            self.stop_button.setVisible(False)
            self.talk_button.setText("Hold to Talk")
            self.talk_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 10px;
                }
                QPushButton:pressed {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #2d2d2d;
                }
            """)
    
    def start_recording(self) -> None:
        """Start recording audio."""
        if not self.recording:
            self.recording = True
            self.frames = []
            
            # Open input stream
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.talk_button.setText("Recording...")
            self.talk_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 10px;
                }
            """)
            self.status_label.setText("Listening...")
            
            # Start recording timer
            self.record_timer = QTimer()
            self.record_timer.timeout.connect(self.record_audio)
            self.record_timer.start(10)  # Check every 10ms
    
    def record_audio(self) -> None:
        """Record a chunk of audio."""
        if self.recording:
            try:
                data = self.input_stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                print(f"Error recording audio: {e}")
    
    def stop_recording(self) -> None:
        """Stop recording and start processing."""
        if self.recording:
            self.recording = False
            self.record_timer.stop()
            
            self.input_stream.stop_stream()
            self.input_stream.close()
            
            self.talk_button.setText("Processing...")
            self.status_label.setText("Processing your request...")
            self.talk_button.setEnabled(False)
            self.stop_button.setVisible(True)  # Show stop button when processing starts
            
            # Convert audio to numpy array
            audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
            audio_data = audio_data.reshape(1, -1)
            
            # Start the audio processor thread
            self.processor = AudioProcessor(
                audio_data=audio_data,
                sample_rate=self.RATE,
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
    
    @Slot(str, str)
    def handle_text_update(self, message_id: str, text: str) -> None:
        """Handle text updates from the audio processor.
        
        Args:
            message_id: The ID of the message being updated
            text: The new text content
        """
        if message_id not in self.current_messages:
            # Create new message if it doesn't exist
            is_user = message_id.endswith("_user")
            message = ChatMessage(text, is_user)
            self.chat_layout.addWidget(message)
            self.current_messages[message_id] = message
            
            # Add to chat history
            self.chat_history.add_message(text, is_user, message_id)
        else:
            # Update existing message
            self.current_messages[message_id].update_text(text)
            # Update chat history
            self.chat_history.add_message(text, message_id.endswith("_user"), message_id)
        
        # Scroll to bottom
        scroll_area = self.chat_container.parent().parent()
        scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().maximum()
        )
    
    @Slot(str, str)
    def handle_processing_finished(self, user_text: str, assistant_text: str) -> None:
        """Handle completion of audio processing.
        
        Args:
            user_text: The transcribed user input
            assistant_text: The generated assistant response
        """
        # Mark assistant message as complete
        assistant_id = f"{id(self)}_assistant"
        if assistant_id in self.current_messages:
            # Get the final text from the current message
            final_text = self.current_messages[assistant_id].text_edit.toPlainText()
            if final_text.strip():
                self.chat_history.complete_message(assistant_id)
        
        # Reset UI state
        self.status_label.setText("Ready to talk")
        self.talk_button.setText("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
            }
        """)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)  # Hide stop button when processing ends
    
    @Slot(str)
    def handle_processing_error(self, error_message: str) -> None:
        """Handle errors during audio processing.
        
        Args:
            error_message: The error message to display
        """
        self.status_label.setText(f"Error: {error_message}")
        self.handle_processing_ended()
    
    @Slot()
    def handle_speaking_started(self) -> None:
        """Handle the start of speech synthesis."""
        self.status_label.setText("Speaking...")
    
    @Slot()
    def handle_speaking_ended(self) -> None:
        """Handle the end of speech synthesis."""
        self.handle_processing_ended()
    
    def handle_processing_ended(self):
        """Handle the end of processing."""
        self.status_label.setText("Ready to talk")
        self.talk_button.setText("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
            }
        """)
        self.talk_button.setEnabled(True)
        self.stop_button.setVisible(False)  # Hide stop button when processing ends
    
    def handle_text_input_keypress(self, event):
        """Handle key press events in the text input box.
        
        Args:
            event: The key press event
        """
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            # Insert new line for Shift+Enter
            self.text_input.insertPlainText("\n")
        elif event.key() == Qt.Key_Return:
            # Submit text for Enter
            text = self.text_input.toPlainText().strip()
            if text:
                self.text_input.clear()
                self.process_text_input(text)
        else:
            # Default behavior for other keys
            QTextEdit.keyPressEvent(self.text_input, event)
    
    def process_text_input(self, text: str) -> None:
        """Process text input from the text box.
        
        Args:
            text: The text to process
        """
        # Add user message immediately
        message_id = f"{id(self)}_user"
        if message_id not in self.current_messages:  # Only add if not already present
            message = ChatMessage(text, True)
            self.chat_layout.addWidget(message)
            self.current_messages[message_id] = message
        
        self.status_label.setText("Processing your request...")
        self.talk_button.setEnabled(False)
        self.stop_button.setVisible(True)  # Show stop button when processing starts
        
        # Start the audio processor thread
        self.processor = AudioProcessor(
            audio_data=None,  # No audio data for text input
            sample_rate=self.RATE,
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
        
        # Start the processor with text input
        self.processor.start(text)
    
    def send_text(self) -> None:
        """Handle text input from the text input field."""
        text = self.text_input.text().strip()
        if text:
            # Clear the input field
            self.text_input.clear()
            
            # Start the audio processor with the text
            self.processor = AudioProcessor(
                audio_data=None,
                sample_rate=self.RATE,
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
            
            # Start the processor with text input
            self.processor.start(text)
            
            # Update UI state
            self.talk_button.setEnabled(False)
            self.stop_button.setVisible(True)  # Show stop button when processing starts
            self.status_label.setText("Processing text input...")
    
    def closeEvent(self, event: Any) -> None:
        """Handle window close event.
        
        Args:
            event: The close event
        """
        if self.recording:
            self.stop_recording()
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
        
        # Save chat history before closing
        self.chat_history.save()
        
        self.audio.terminate()
        event.accept() 