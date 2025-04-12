"""Agent module.

This module provides the RWBAgent class for handling LLM inference
and streaming responses, separate from audio processing.
"""

from typing import Iterator, List, Dict, Any
import asyncio
from textwrap import dedent
from datetime import datetime

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.wikipedia import WikipediaTools


#MODEL= "phi4:latest"
#MODEL="mistral-small3.1"
MODEL = "qwen2.5:14b-instruct-q8_0"
#MODEL= "granite3.2:8b-instruct-q8_0"


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
            model=Ollama(id=self.model_name),
            add_history_to_messages=True,
            # Number of historical responses to add to the messages.
            num_history_responses=5,
            read_chat_history=True,
            tools=[DuckDuckGoTools(), PubmedTools(), WikipediaTools(), PythonTools()],
            instructions=dedent("""You are a helpful assistant able to choose and use tools when appropriate.
            If you are not confident that you can answer the user with confidence, select the most appropriate tool
            to answer. Be concise in your answer, and use markdown format where appropriate.
            Today's date is {datetime.now().strftime('%Y-%m-%d')}.
            
            When using tools, ALWAYS use JSON format for tool calls like this:
            ```json
            {
              "arguments": { ... },
              "name": "tool_name"
            }
            ```
            
            DO NOT use XML-style tool calls like <tool_call> or </tool_call>.
            After using a tool, always provide a helpful response based on the tool's output."""),
            show_tool_calls=True,
            markdown=True,
        )
    
    def astream(self, prompt: str) -> Iterator[str]:
        """Stream responses from the LLM with absolute minimal latency.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            str: Chunks of the LLM's response
        """
        print(f"[DEBUG] astream called with prompt: {prompt[:30]}...")
        # Check if memory exists before trying to access its messages
        if hasattr(self.agent, 'memory'):
            if self.agent.memory:
                print(f"Agent memory dump: {[m.model_dump(include={"role", "content"}) for m in self.agent.memory.messages]}")
            else:
                print("Agent memory is empty")
        else:
            print("Agent memory not initialized yet")
        
        # Direct streaming with maximum performance
        stream = self.agent.run(prompt, 
                                stream=True,
                                stream_intermediate_steps=True,
        )
        
        
        # Minimal tool call detection - only the bare minimum checks needed
        # in_tool_call = False
        
        # Process each chunk immediately - minimal processing for maximum speed
        for chunk in stream:
            match(chunk.event):
                case 'RunResponse':
                    yield chunk.content
                case 'RunStarted':
                    print(f"Run started: {chunk.content}")
                case 'ToolCallStarted':
                    print(f"Tool call started: {chunk.content}")
                case 'ToolCallCompleted':
                    print(f"Tool call completed: {chunk.content}")
                case 'UpdatingMemory':
                    print(f"Updating memory...")
                case 'FinalResponse':
                    print(f"Final response: {chunk.content}")
                case _:    
                    print(f"Unknown event: {chunk.event}")

            # # Only process content chunks
            # if not hasattr(chunk, 'content') or chunk.content is None:
            #     continue
                
            # content = chunk.content
            # if not isinstance(content, str):
            #     continue
            
            # # Ultra-fast tool call detection
            # if in_tool_call:
            #     # Only check for end of tool call
            #     if "</tool_call>" in content or "```" in content or "}" in content:
            #         in_tool_call = False
            #     continue
            
            # # Check for start of tool call with absolute minimal checks
            # if "<tool_call>" in content or "```json" in content or ('{' in content and '"name":' in content):
            #     in_tool_call = True
            #     continue
            
            # # Yield immediately for lowest latency
            # yield content
                
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