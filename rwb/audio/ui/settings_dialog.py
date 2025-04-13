"""Settings dialog module.

This module provides a dialog for configuring application settings.
"""
from dotenv import load_dotenv
import os

load_dotenv()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:14b-instruct-q8_0")

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QFormLayout, QComboBox, QGroupBox
)
from PySide6.QtCore import QSettings, Qt

from rwb.llm.ollamamodels import list_models

class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None):
        """Initialize the settings dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        
        # Initialize settings
        self.settings = QSettings("RWB", "VoiceAssistant")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # User Settings Group
        user_group = QGroupBox("User Settings")
        user_layout = QFormLayout()
        
        # User name field
        self.username_edit = QLineEdit()
        self.username_edit.setText(self.settings.value("user/name", ""))
        user_layout.addRow("Name:", self.username_edit)
        
        # User email field
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.settings.value("user/email", ""))
        user_layout.addRow("Email:", self.email_edit)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # Model Settings Group
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout()
        
        # Model name field (combobox)
        self.model_combo = QComboBox()
        models = list_models()
        if not models:
            models = ["qwen2.5:14b-instruct-q8_0", "mistral-small3.1", "granite3.2:8b-instruct-q8_0"]
        self.model_combo.addItems(models)
        current_model = self.settings.value("model/name", DEFAULT_MODEL)
        index = self.model_combo.findText(current_model)
        self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        model_layout.addRow("Model Name:", self.model_combo)
        
        # TTS voice field (combobox)
        self.voice_combo = QComboBox()
        voices = ["bf_emma", "af_heart", "af_bella", "bm_daniel", "bm_lewis"]
        self.voice_combo.addItems(voices)
        current_voice = self.settings.value("tts/voice", voices[0])
        index = self.voice_combo.findText(current_voice)
        self.voice_combo.setCurrentIndex(index if index >= 0 else 0)
        model_layout.addRow("TTS Voice:", self.voice_combo)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Handle dialog acceptance and save settings."""
        # Save user settings
        self.settings.setValue("user/name", self.username_edit.text())
        self.settings.setValue("user/email", self.email_edit.text())
        
        # Save model settings
        self.settings.setValue("model/name", self.model_combo.currentText())
        self.settings.setValue("tts/voice", self.voice_combo.currentText())
        
        # Accept dialog
        super().accept()
