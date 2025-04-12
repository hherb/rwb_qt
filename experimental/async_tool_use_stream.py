"""Run `pip install duckduckgo-search` to install dependencies."""

import asyncio

from agno.agent import Agent
from agno.models.ollama import OllamaTools
from agno.tools.duckduckgo import DuckDuckGoTools

#MODEL = "granite3.2:8b-instruct-q8_0"
MODEL= "phi4:latest"
#MODEL= ""

agent = Agent(
    model=OllamaTools(id=MODEL),
    tools=[DuckDuckGoTools()],
    show_tool_calls=False,
    markdown=True,
)
#asyncio.run(agent.aprint_response("What is happening in Germany today", stream=True))
if __name__ == "__main__":
    async def main():
        stream = agent.run("What is happening in Germany today",
            stream=True,
            #stream_intermediate_steps=True,
        )
        for chunk in stream:
            # Print content if available
            if hasattr(chunk, 'content') and chunk.content is not None:
                print(chunk.content, end="")
            # Print tool calls if available
            #elif hasattr(chunk, 'tool_calls') and chunk.tool_calls is not None:
            #    print(f"Tool calls: {chunk.tool_calls}", end="")
            # Print final response if available
            #elif hasattr(chunk, 'final_response') and chunk.final_response is not None:
            #    print(f"Final response: {chunk.final_response}", end="")
       
                
    
    asyncio.run(main())