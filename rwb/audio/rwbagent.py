"""Agent module.

This module provides the RWBAgent class for handling LLM inference
and streaming responses, separate from audio processing.
"""

from typing import Iterator, List, Dict, Any
from ollama import chat

class RWBAgent:
    """Handles LLM inference and streaming responses."""
    
    def __init__(self, model_name: str = 'granite3.2:8b-instruct-q8_0'):
        """Initialize the agent.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
    
    def astream(self, prompt: str) -> Iterator[str]:
        """Stream responses from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            str: Chunks of the LLM's response
        """
        for response in chat(model=self.model_name, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], stream=True):
            if 'message' in response and 'content' in response['message']:
                yield response['message']['content']
                
    def get_model_name(self) -> str:
        """Get the current model name.
        
        Returns:
            str: The name of the LLM model being used
        """
        return self.model_name
    
    def set_model_name(self, model_name: str) -> None:
        """Set a new model name.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name