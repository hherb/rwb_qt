"""Agent module.

This module provides the RWBAgent class for handling LLM inference
and streaming responses, separate from audio processing.
"""

from typing import Iterator, List, Dict, Any
import asyncio

from agno.agent import Agent
from agno.models.ollama import OllamaTools
from agno.tools.duckduckgo import DuckDuckGoTools

MODEL= "phi4:latest"


class RWBAgent:
    """Handles LLM inference and streaming responses."""
    
    def __init__(self, model_name: str = MODEL):
        """Initialize the agent.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
        print(f"Initializing RWBAgent with model: {self.model_name}")
        self.agent = Agent(
            model=OllamaTools(id=self.model_name),
            tools=[DuckDuckGoTools()],
            show_tool_calls=False,
            markdown=True,
        )
    
    def astream(self, prompt: str) -> Iterator[str]:
        """Stream responses from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            str: Chunks of the LLM's response
        """
        print(f"show_tool_calls is set to: {self.agent.show_tool_calls}")
        stream = self.agent.run(prompt, stream=True)
        for chunk in stream:
            # Skip tool call chunks completely
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                continue
            
            # Only yield content if it exists
            if hasattr(chunk, 'content') and chunk.content is not None:
                yield chunk.content

                
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


if __name__ == "__main__":
    agent = RWBAgent()
    prompt = "What is happening in Germany today"
    for chunk in agent.astream(prompt):
        # Print content if available
        print(chunk, end="")
    print("\n--- End of Stream ---")