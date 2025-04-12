"""🗽 Agent with Tools - Your AI News Buddy that can search the web

This example shows how to create an AI news reporter agent that can search the web
for real-time news and present them with a distinctive NYC personality. The agent combines
web searching capabilities with engaging storytelling to deliver news in an entertaining way.

Run `pip install openai duckduckgo-search agno` to install dependencies.
"""

import asyncio
import json
from textwrap import dedent
from pprint import pprint

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools

MODEL="mistral-small3.1"  # You can choose any model you like
#MODEL="granite3.2:8b-instruct-q8_0"  # You can choose any model you like
# Create a News Reporter Agent with a fun personality
agent = Agent(
    model=Ollama(id=MODEL),  # You can choose any model you like
    instructions=dedent("""\
        You are a web researcher 🗽
        Your task is to search teh web for accurate information
        Follow these guidelines for every report:
        1. Start with an attention-grabbing headline using relevant emoji
        2. Use the search tool to find current, accurate information
        3. Keep responses concise but informative (2-3 paragraphs max)

        Remember: Always verify facts through web searches and cite your sources!\
    """),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    
    markdown=True,
    stream=True,
    #debug_mode=True,  # Enable debug mode for additional information
)


print(f"Running agent with model: {MODEL}")

async def main():
    stream = agent.run(
        "What did Dr Horst Herb do Australia?",
        stream=True,
        stream_intermediate_steps=True,
        #show_intermediate_steps=True,
    )
    for chunk in stream:
        match(chunk.event):
            case 'RunResponse':
                print(f"Run response: {chunk.content}")
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

        if hasattr(chunk, 'context'):
            print('CONTEXT')
            pprint(chunk.context)

        if hasattr(chunk, 'event_data'):
            print('EVENT DATA')
            pprint(chunk.event_data)

        if hasattr(chunk, 'messages'):
            if chunk.messages:
                for message in chunk.messages:
                    if message.role == 'tool':
                        messages = message.content
                        msglist = json.loads(messages)
                        pprint(msglist)
                        for msg in msglist:
                            print(f"Title: {msg.get('title', 'N/A')}")
                            print(f"URL: {msg.get('href'), 'no URL'}")

        
            
        #pprint(chunk)
        print(f"\n{'_' * 80}\n")
        # if hasattr(chunk, 'tool_calls') and chunk.tool_calls is not None:
        #     print(f"Tool calls: {chunk.tool_calls}", end="")
        # if hasattr(chunk, 'content') and chunk.content is not None:
        #     print(chunk.content, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())


