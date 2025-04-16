"""Settings dialog module.

This module provides a dialog for configuring application settings.
"""
from dotenv import load_dotenv
import os
import json

load_dotenv()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:14b-instruct-q8_0")

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QFormLayout, QComboBox, QGroupBox,
    QTextEdit, QTabWidget, QWidget, QSizePolicy
)
from PySide6.QtCore import QSettings, Qt

# Import our context manager for user and assistant settings
from rwb.context import context_manager, User, Assistant

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
        self.resize(500, 400)
        
        # Initialize settings
        self.settings = QSettings("RWB", "ResearchWithoutBorders")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create tab widget for different settings categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # --- User Settings Tab ---
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        
        # Get current user settings from context manager
        user = context_manager.user
        
        # User profile settings
        user_group = QGroupBox("User Profile")
        user_form = QFormLayout()
        # Make form layout fields stretch
        user_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Title field
        self.title_edit = QLineEdit()
        self.title_edit.setText(user.title)
        self.title_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        user_form.addRow("Title:", self.title_edit)
        
        # First name field
        self.firstname_edit = QLineEdit()
        self.firstname_edit.setText(user.firstname)
        self.firstname_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        user_form.addRow("First Name:", self.firstname_edit)
        
        # Last name field
        self.surname_edit = QLineEdit()
        self.surname_edit.setText(user.surname)
        self.surname_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        user_form.addRow("Last Name:", self.surname_edit)
        
        # Email field
        self.email_edit = QLineEdit()
        self.email_edit.setText(user.email)
        self.email_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        user_form.addRow("Email:", self.email_edit)
        
        # Background field (multi-line)
        self.background_edit = QTextEdit()
        self.background_edit.setText(user.background)
        self.background_edit.setMaximumHeight(100)
        self.background_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        user_form.addRow("Background:", self.background_edit)
        
        user_group.setLayout(user_form)
        user_layout.addWidget(user_group)
        
        # Add user tab to tab widget
        self.tab_widget.addTab(user_tab, "User Settings")
        
        # --- Assistant Settings Tab ---
        assistant_tab = QWidget()
        assistant_layout = QVBoxLayout(assistant_tab)
        
        # Get current assistant settings from context manager
        assistant = context_manager.assistant
        
        # Assistant settings
        assistant_group = QGroupBox("Assistant Profile")
        assistant_form = QFormLayout()
        # Make form layout fields stretch
        assistant_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Assistant name field
        self.assistant_name_edit = QLineEdit()
        self.assistant_name_edit.setText(assistant.name)
        self.assistant_name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        assistant_form.addRow("Name:", self.assistant_name_edit)
        
        # Assistant background field
        self.assistant_background_edit = QTextEdit()
        self.assistant_background_edit.setText(assistant.background)
        self.assistant_background_edit.setMaximumHeight(100)
        self.assistant_background_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        assistant_form.addRow("Background:", self.assistant_background_edit)
        
        # Assistant base prompt field
        self.base_prompt_edit = QTextEdit()
        self.base_prompt_edit.setText(assistant.base_prompt)
        self.base_prompt_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        assistant_form.addRow("Base Prompt:", self.base_prompt_edit)
        
        assistant_group.setLayout(assistant_form)
        assistant_layout.addWidget(assistant_group)
        
        # Add assistant tab to tab widget
        self.tab_widget.addTab(assistant_tab, "Assistant Settings")
        
        # --- Model Settings Tab ---
        model_tab = QWidget()
        model_layout = QVBoxLayout(model_tab)
        
        # Model settings group
        model_group = QGroupBox("Model Settings")
        model_form = QFormLayout()
        # Make form layout fields stretch
        model_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Model name field (combobox)
        self.model_combo = QComboBox()
        models = list_models()
        if not models:
            models = ["qwen2.5:14b-instruct-q8_0", "mistral-small3.1", "granite3.2:8b-instruct-q8_0"]
        self.model_combo.addItems(models)
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Get current model from context manager
        current_model = context_manager.model_name
        index = self.model_combo.findText(current_model)
        self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        model_form.addRow("Model Name:", self.model_combo)
        
        # TTS voice field (combobox)
        self.voice_combo = QComboBox()
        voices = ["bf_emma", "af_heart", "af_bella", "bm_daniel", "bm_lewis"]
        self.voice_combo.addItems(voices)
        self.voice_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Get current voice from context manager
        current_voice = context_manager.tts_voice
        index = self.voice_combo.findText(current_voice)
        self.voice_combo.setCurrentIndex(index if index >= 0 else 0)
        model_form.addRow("TTS Voice:", self.voice_combo)
        
        model_group.setLayout(model_form)
        model_layout.addWidget(model_group)
        
        # Add model tab to tab widget
        self.tab_widget.addTab(model_tab, "Model Settings")
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Handle dialog acceptance and save settings."""
        # Create and save user settings
        user = User(
            title=self.title_edit.text(),
            firstname=self.firstname_edit.text(),
            surname=self.surname_edit.text(),
            email=self.email_edit.text(),
            background=self.background_edit.toPlainText()
        )
        context_manager.save_user(user)
        
        # Create and save assistant settings
        assistant = Assistant(
            name=self.assistant_name_edit.text(),
            background=self.assistant_background_edit.toPlainText(),
            base_prompt=self.base_prompt_edit.toPlainText()
        )
        context_manager.save_assistant(assistant)
        
        # Save model settings using the context manager
        context_manager.model_name = self.model_combo.currentText()
        context_manager.tts_voice = self.voice_combo.currentText()
        
        # Accept dialog
        super().accept()
