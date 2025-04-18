"""🔍 Research Agent - Your AI Investigative Journalist!

This example shows how to create a sophisticated research agent that combines
web search capabilities with professional journalistic writing skills. The agent performs
comprehensive research using multiple sources, fact-checks information, and delivers
well-structured, NYT-style articles on any topic.

Key capabilities:
- Advanced web search across multiple sources
- Content extraction and analysis
- Cross-reference verification
- Professional journalistic writing
- Balanced and objective reporting

Example prompts to try:
- "Analyze the impact of AI on healthcare delivery and patient outcomes"
- "Report on the latest breakthroughs in quantum computing"
- "Investigate the global transition to renewable energy sources"
- "Explore the evolution of cybersecurity threats and defenses"
- "Research the development of autonomous vehicle technology"

Dependencies: `pip install openai duckduckgo-search newspaper4k lxml_html_clean agno`
"""

from textwrap import dedent

from agno.agent import Agent
from agno.models.ollama import Ollama as ChatModel
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools
#MODEL="mistral-small3.1"
MODEL="granite3.2:8b-instruct-q8_0"

# Initialize the research agent with advanced journalistic capabilities
research_agent = Agent(
    model=ChatModel(id=MODEL),
    tools=[DuckDuckGoTools(), Newspaper4kTools()],
    description=dedent("""\
        You are an elite investigative journalist with decades of experience at the New York Times.
        Your expertise encompasses: 📰

        - Deep investigative research and analysis
        - Meticulous fact-checking and source verification
        - Compelling narrative construction
        - Data-driven reporting and visualization
        - Expert interview synthesis
        - Trend analysis and future predictions
        - Complex topic simplification
        - Ethical journalism practices
        - Balanced perspective presentation
        - Global context integration\
    """),
    instructions=dedent("""\
        1. Research Phase 🔍
           - Search for 10+ authoritative sources on the topic
           - Prioritize recent publications and expert opinions
           - Identify key stakeholders and perspectives

        2. Analysis Phase 📊
           - Extract and verify critical information
           - Cross-reference facts across multiple sources
           - Identify emerging patterns and trends
           - Evaluate conflicting viewpoints

        3. Writing Phase ✍️
           - Craft an attention-grabbing headline
           - Structure content in NYT style
           - Include relevant quotes and statistics
           - Maintain objectivity and balance
           - Explain complex concepts clearly

        4. Quality Control ✓
           - Verify all facts and attributions
           - Ensure narrative flow and readability
           - Add context where necessary
           - Include future implications
    """),
    expected_output=dedent("""\
        # {Compelling Headline} 📰

        ## Executive Summary
        {Concise overview of key findings and significance}

        ## Background & Context
        {Historical context and importance}
        {Current landscape overview}

        ## Key Findings
        {Main discoveries and analysis}
        {Expert insights and quotes}
        {Statistical evidence}

        ## Impact Analysis
        {Current implications}
        {Stakeholder perspectives}
        {Industry/societal effects}

        ## Future Outlook
        {Emerging trends}
        {Expert predictions}
        {Potential challenges and opportunities}

        ## Expert Insights
        {Notable quotes and analysis from industry leaders}
        {Contrasting viewpoints}

        ## Sources & Methodology
        {List of primary sources with key contributions}
        {Research methodology overview}

        ---
        Research conducted by AI Investigative Journalist
        New York Times Style Report
        Published: {current_date}
        Last Updated: {current_time}\
    """),
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
)

# Example usage with detailed research request
if __name__ == "__main__":
    stream = research_agent.run(
        "Analyze the current state and future implications of artificial intelligence regulation worldwide",
        stream=True,
        stream_intermediate_steps=True,
    )
    for chunk in stream:
        # Print summary of each chunk type
        print("\n--- New Chunk ---")
        print(f"Event: {chunk.event}")
        
        # Print content if available
        if hasattr(chunk, 'content') and chunk.content is not None:
            print(f"Content: {chunk.content}")
        
        # Print tool calls if available
        if hasattr(chunk, 'formatted_tool_calls') and chunk.formatted_tool_calls:
            print(f"Tool Calls: {chunk.formatted_tool_calls}")
        
        # Print messages if available
        if hasattr(chunk, 'messages') and chunk.messages:
            print(f"Messages: {chunk.messages}")
            
        # Print context for RAG if available
        if hasattr(chunk, 'context') and chunk.context:
            print(f"Context: {chunk.context}")
            
        # Print metrics if available
        if hasattr(chunk, 'metrics') and chunk.metrics:
            print(f"Metrics: {chunk.metrics}")
            
        # Print thinking if available
        if hasattr(chunk, 'thinking') and chunk.thinking:
            print(f"Thinking: {chunk.thinking}")
            
        print("-------------------")
    

# Advanced research topics to explore:
"""
Technology & Innovation:
1. "Investigate the development and impact of large language models in 2024"
2. "Research the current state of quantum computing and its practical applications"
3. "Analyze the evolution and future of edge computing technologies"
4. "Explore the latest advances in brain-computer interface technology"

Environmental & Sustainability:
1. "Report on innovative carbon capture technologies and their effectiveness"
2. "Investigate the global progress in renewable energy adoption"
3. "Analyze the impact of circular economy practices on global sustainability"
4. "Research the development of sustainable aviation technologies"

Healthcare & Biotechnology:
1. "Explore the latest developments in CRISPR gene editing technology"
2. "Analyze the impact of AI on drug discovery and development"
3. "Investigate the evolution of personalized medicine approaches"
4. "Research the current state of longevity science and anti-aging research"

Societal Impact:
1. "Examine the effects of social media on democratic processes"
2. "Analyze the impact of remote work on urban development"
3. "Investigate the role of blockchain in transforming financial systems"
4. "Research the evolution of digital privacy and data protection measures"
"""