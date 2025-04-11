"""Chat history management module.

This module handles the serialization and deserialization of chat history,
including saving messages to files and managing the current chat session.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from .chat_message import MessageSender

class ChatHistory:
    """Handles chat history serialization and deserialization."""
    
    def __init__(self):
        self.history_dir = Path.home() / ".rwb" / "chat_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.current_chat: List[Dict[str, Any]] = []
        self.pending_messages: Dict[str, Dict[str, Any]] = {}  # Track incomplete messages
    
    def add_message(self, text: str, sender: MessageSender, message_id: str) -> None:
        """Add a message to the current chat history.
        
        Args:
            text: The message text
            sender: The type of sender (user, assistant, system, etc.)
            message_id: Unique identifier for the message
        """
        # Skip empty messages
        if not text.strip():
            return
            
        # For user messages, save immediately
        if sender == MessageSender.USER:
            self.current_chat.append({
                "text": text,
                "sender": sender.value,
                "timestamp": datetime.now().isoformat()
            })
        else:
            # For other messages, only update the pending message
            self.pending_messages[message_id] = {
                "text": text,
                "sender": sender.value,
                "timestamp": datetime.now().isoformat()
            }
    
    def complete_message(self, message_id: str) -> None:
        """Mark a message as complete and add it to the chat history.
        
        Args:
            message_id: The ID of the message to complete
        """
        if message_id in self.pending_messages:
            message = self.pending_messages.pop(message_id)
            if message["text"].strip():  # Only add non-empty messages
                self.current_chat.append(message)
    
    def save(self) -> None:
        """Save the current chat history to a file."""
        if not self.current_chat:
            return
            
        # Use current time for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.history_dir / f"chat_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.current_chat, f, indent=2)
        
        # Clear current chat after saving
        self.current_chat = []
        self.pending_messages = {} 