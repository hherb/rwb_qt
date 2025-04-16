"""Context module for RWB application.

This module provides classes and functionality for managing user and assistant context,
including persistence of user preferences and settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QSettings


class User:
    """User information class for the RWB application."""
    
    def __init__(self, title: str = "", firstname: str = "", surname: str = "", 
                 email: str = "", background: str = ""):
        """Initialize a user.
        
        Args:
            title: User's title (Dr., Prof., etc.)
            firstname: User's first name
            surname: User's last name
            email: User's email address
            background: Brief description of user's background
        """
        self.title = title
        self.firstname = firstname
        self.surname = surname
        self.email = email
        self.background = background
    
    def to_dict(self) -> Dict[str, str]:
        """Convert user information to dictionary for storage.
        
        Returns:
            Dictionary representation of the user
        """
        return {
            "title": self.title,
            "firstname": self.firstname,
            "surname": self.surname,
            "email": self.email,
            "background": self.background
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'User':
        """Create a User instance from a dictionary.
        
        Args:
            data: Dictionary with user information
            
        Returns:
            User instance populated with the data
        """
        return cls(
            title=data.get("title", ""),
            firstname=data.get("firstname", ""),
            surname=data.get("surname", ""),
            email=data.get("email", ""),
            background=data.get("background", "")
        )


class Assistant:
    """Assistant settings for the RWB application."""
    
    def __init__(self, name: str = "Emily", 
                 background: str = "I am an AI research assistant.",
                 base_prompt: str = ""):
        """Initialize assistant settings.
        
        Args:
            name: Assistant's name
            background: Assistant's background/persona description
            base_prompt: Base system prompt to include in all interactions
        """
        self.name = name
        self.background = background
        self.base_prompt = base_prompt
    
    def to_dict(self) -> Dict[str, str]:
        """Convert assistant settings to dictionary for storage.
        
        Returns:
            Dictionary representation of settings
        """
        return {
            "name": self.name,
            "background": self.background,
            "base_prompt": self.base_prompt
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Assistant':
        """Create an Assistant instance from a dictionary.
        
        Args:
            data: Dictionary with assistant settings
            
        Returns:
            Assistant instance populated with the data
        """
        return cls(
            name=data.get("name", "Emily"),
            background=data.get("background", "I am an AI research assistant."),
            base_prompt=data.get("base_prompt", "")
        )


class ContextManager:
    """Manages saving and loading of user and assistant settings."""
    
    def __init__(self):
        """Initialize the context manager."""
        self.settings = QSettings("RWB", "ResearchWithoutBorders")
        self._user = None
        self._assistant = None
        self._model_name = None
        self._tts_voice = None
        
        # Load settings on initialization
        self.load_settings()
    
    def load_settings(self):
        """Load user and assistant settings from storage."""
        # Load user settings
        user_json = self.settings.value("user", "{}")
        try:
            user_data = json.loads(user_json)
            self._user = User.from_dict(user_data)
        except (json.JSONDecodeError, TypeError):
            # Default user if settings are invalid or not found
            self._user = User(
                title="Dr.",
                firstname="Horst",
                surname="Herb",
                email=os.getenv("AUTHOR_EMAIL", "default@example.com"),
                background="I am a medical professional with a background in medicine and research."
            )
            # Save the default user
            self.save_user(self._user)
        
        # Load assistant settings
        assistant_json = self.settings.value("assistant", "{}")
        try:
            assistant_data = json.loads(assistant_json)
            self._assistant = Assistant.from_dict(assistant_data)
        except (json.JSONDecodeError, TypeError):
            # Default assistant if settings are invalid or not found
            self._assistant = Assistant(
                name="Emily",
                background="I am an AI research assistant specialized in medical and scientific research.",
                base_prompt=""
            )
            # Save the default assistant
            self.save_assistant(self._assistant)
            
        # Load model settings
        default_model = os.getenv("DEFAULT_MODEL", "qwen2.5:14b-instruct-q8_0")
        self._model_name = self.settings.value("model/name", default_model)
        self._tts_voice = self.settings.value("tts/voice", "bf_emma")
    
    def save_user(self, user: User) -> None:
        """Save user settings to storage.
        
        Args:
            user: User instance to save
        """
        self._user = user
        self.settings.setValue("user", json.dumps(user.to_dict()))
    
    def save_assistant(self, assistant: Assistant) -> None:
        """Save assistant settings to storage.
        
        Args:
            assistant: Assistant instance to save
        """
        self._assistant = assistant
        self.settings.setValue("assistant", json.dumps(assistant.to_dict()))
    
    @property
    def user(self) -> User:
        """Get the current user.
        
        Returns:
            User instance with current settings
        """
        if self._user is None:
            self.load_settings()
        return self._user
    
    @property
    def assistant(self) -> Assistant:
        """Get the current assistant settings.
        
        Returns:
            Assistant instance with current settings
        """
        if self._assistant is None:
            self.load_settings()
        return self._assistant
    
    @property
    def model_name(self) -> str:
        """Get the current model name.
        
        Returns:
            Name of the currently selected model
        """
        if self._model_name is None:
            self.load_settings()
        return self._model_name
    
    @model_name.setter
    def model_name(self, name: str) -> None:
        """Set and save the model name.
        
        Args:
            name: Name of the model to set
        """
        self._model_name = name
        self.settings.setValue("model/name", name)
    
    @property
    def tts_voice(self) -> str:
        """Get the current TTS voice.
        
        Returns:
            Name of the currently selected TTS voice
        """
        if self._tts_voice is None:
            self.load_settings()
        return self._tts_voice
    
    @tts_voice.setter
    def tts_voice(self, voice: str) -> None:
        """Set and save the TTS voice.
        
        Args:
            voice: Name of the TTS voice to set
        """
        self._tts_voice = voice
        self.settings.setValue("tts/voice", voice)


# Create a singleton instance for easy access throughout the application
context_manager = ContextManager()
