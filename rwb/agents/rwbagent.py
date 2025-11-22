"""Agent module.

This module provides the RWBAgent class for handling LLM inference
and streaming responses, separate from audio processing.
"""
import os
import pathlib
from typing import Iterator, AsyncIterator, List, Dict, Any, Union
import asyncio
from textwrap import dedent
from datetime import datetime
import json
from pprint import pprint
from dotenv import load_dotenv
import random

from PySide6.QtCore import QObject, Signal, QThreadPool

# Import the context manager for user and assistant settings
from rwb.context import context_manager

from rwb.agents.worker import InputProcessorWorker

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools
#from agno.tools.pubmed import PubmedTools. #it sucks
from rwb.tools.pubmed import PubMedTools
from agno.tools.python import PythonTools
from agno.tools.wikipedia import WikipediaTools
from agno.tools.website import WebsiteTools


#MODEL= "phi4:latest"
#MODEL="mistral-small3.1"
MODEL = "qwen2.5:14b-instruct-q8_0"
#MODEL= "granite3.2:8b-instruct-q8_0"
# Load environment variables from .env file
load_dotenv()
AUTHOR_EMAIL = os.getenv("AUTHOR_EMAIL") or "default@example.com"
print(f"Author email: {AUTHOR_EMAIL}")

PYTHONTOOLS_BASEDIR = pathlib.Path("~/.rwbtmp/python").expanduser()
if not PYTHONTOOLS_BASEDIR.exists():
    os.makedirs(PYTHONTOOLS_BASEDIR, exist_ok=True)

RESEARCHING_FEEDBACKS= ["OK, researching now",
                       "OK, let me check that",
                       "Hang on, I am looking for it",
                       "OK, let me check that for you",
                       "Searching for you now",
                       "Yes, let me find that for you",
                       "I am looking for it now",
                       "Allright, let me check that for you",
                       "Searching for you now",
                       "Understood, let me find that for you",
                       "I am looking for it now",
]

    
RESEARCH_COMPLETED_FEEDBACKS = ["I found something. Processing it now",
                                "Got results, analyzing them now",
                                "Found something, let me check it",
                                "Search succesful, need time to analyze",
                                "Interesting results, analyzing now",
                                "Give me some time to look at the results",
                                "I found something, let me check it",
                                "Sorry, will take a while processing the results",

]


def random_choice(choices: List[str]) -> str:
    """Randomly select a choice from the provided list.
    
    Args:
        choices: List of choices to select from
        
    Returns:
        str: A randomly selected choice
    """
    if not choices:
        return ""
    return random.choice(choices)

class RWBAgent(QObject):
    """Handles LLM inference and streaming responses."""
    
    # Signal definitions
    feedback = Signal(str, str)  # Emits (message, type)
    text_update = Signal(str, str)  # Emits (message_id, text)
    processing_complete = Signal()  # Emits when processing is complete
    
    def __init__(self, model_name: str = None):
        """Initialize the RWBAgent.
        
        Args:
            model_name: The name of the LLM model to use (optional)
        """
        super().__init__()
        self.model_name = model_name or "mistral-small3.1"
        self.audio_processor = None
        self.current_audio_data = None
        self.conversation_history = []
        self.current_message_id = ""
        self.saved_mute_state = False  # Track mute state across STT processing
        
        # Initialize the model
        self._send_feedback(f"Initializing RWBAgent with model: {self.model_name}", "info")
        self.agent = Agent(
            model=Ollama(id=self.model_name),
            add_history_to_messages=True,
            # Number of historical responses to add to the messages.
            num_history_responses=5,
            read_chat_history=True,
            tools=[DuckDuckGoTools(), 
                   WebsiteTools(),
                   PubMedTools(email=self.get_user().email, max_results=20), 
                   WikipediaTools(), 
                   PythonTools(base_dir=PYTHONTOOLS_BASEDIR)],
            instructions=dedent(self._build_instructions()),
            show_tool_calls=True,
            markdown=True,
        )
    
    def _build_instructions(self):
        """Build the base instructions for the agent using context manager data.
        
        Returns:
            str: The constructed base instructions
        """
        # Get user and assistant settings from context manager
        user = self.get_user()
        assistant = context_manager.assistant
        
        # Building the prompt with user and assistant settings
        base_instructions = f"""Your name is {assistant.name}. Today's actual date is {datetime.now().strftime('%Y-%m-%d')}.
            I am {user.title} {user.firstname} {user.surname}. You may address me as {user.firstname}.
            You are a helpful research assistant able to choose and use tools when appropriate.
            {assistant.background}
            
            If you are not confident that you can answer the user with confidence, select the most appropriate tool
            to answer. Be concise in your answer.
            I often use a voice interface to communicate with you. Sometimes the resulting text is distorted.
            I often ask to search for information on PubMed, but this is sometimes transcribed as "popmat" or similar.
            So, if it is medicine and search related and vaguealy would sound like "pubmed", use PubMed.
            If you are not sure about the text, ask me to repeat it.
            After using a tool, always provide a helpful response based on the tool's output.
            If the tool does not yield useful context, try the next likely tool that might give and answer.
            If you have exhuasted your tools and still did not find the answer, tell me that you did not find an answer."""
        
        # Add any custom base prompt if available
        if assistant.base_prompt:
            base_instructions += f"\n\n{assistant.base_prompt}"
        
        return base_instructions
    
    def get_user(self) -> Any:
        """Get user information from settings.
        
        Returns:
            User object with title, firstname, surname, and other attributes
        """
        # Get user from context manager (will load from settings)
        return context_manager.user

    
    def set_audio_processor(self, processor) -> None:
        """Set the audio processor.
        
        Args:
            processor: The AudioProcessor instance
        """
        self.audio_processor = processor
    
    def process_user_input(self, input_text: str) -> None:
        """Process text input from user and generate a response.
        
        Args:
            input_text: The text input from the user
        """
        # Ensure we preserve mute state that might have been set earlier
        # This fixes the issue where voice-to-text processing resets mute settings
        if hasattr(self, 'saved_mute_state') and self.audio_processor:
            # Restore the saved mute state to ensure it persists through STT processing
            self.audio_processor.set_mute_state(self.saved_mute_state)
        self.current_message_id = str(id(input_text))  # Generate a unique ID for this message
        
        # Start processing the user input
        self._send_feedback(f"Processing query: {input_text[:30]}...", "debug")
        
        # Initialize the accumulated response text
        self.assistant_text = ""
        
        # Create worker to process input in a separate thread
        self.input_worker = InputProcessorWorker(self.astream, input_text)
        
        # Connect signals for handling responses
        self.input_worker.signals.chunk.connect(self._on_chunk_received)
        self.input_worker.signals.sentence_ready.connect(self._process_sentence)
        self.input_worker.signals.error.connect(lambda error: self._send_feedback(f"Error: {error}", "error"))
        self.input_worker.signals.finished.connect(self._on_processing_finished)
        
        # Start the worker
        QThreadPool.globalInstance().start(self.input_worker)
        
    async def process_user_input_async(self, input_text: str) -> None:
        """Process text input from user asynchronously and generate a response.
        
        Args:
            input_text: The text input from the user
        """
        # Ensure we preserve mute state that might have been set earlier
        if hasattr(self, 'saved_mute_state') and self.audio_processor:
            self.audio_processor.set_mute_state(self.saved_mute_state)
        
        self.current_message_id = str(id(input_text))  # Generate a unique ID for this message
        
        # Start processing the user input
        self._send_feedback(f"Processing query asynchronously: {input_text[:30]}...", "debug")
        
        # Initialize the accumulated response text
        self.assistant_text = ""
        
        try:
            from rwb.audio.processor import split_into_sentences
            
            # Process asynchronously
            async for chunk in await self.astream_async(input_text):
                if chunk:
                    # Update the accumulated text
                    self.assistant_text += chunk
                    
                    # Update the UI with the accumulated text
                    assistant_message_id = f"{self.current_message_id}_assistant"
                    self.text_update.emit(assistant_message_id, self.assistant_text)
                    
                    # Process complete sentences for TTS if audio processor is available
                    if self.audio_processor:
                        # Split current text into sentences
                        sentences = split_into_sentences(chunk)
                        for sentence in sentences:
                            if sentence.strip():
                                # Process each complete sentence
                                self._process_sentence(sentence.strip())
                                
                    # Allow the event loop to process other events
                    await asyncio.sleep(0)
                    
            # Process is complete
            self._on_processing_finished()
            
        except Exception as e:
            error_msg = f"Error in async processing: {str(e)}"
            self._send_feedback(error_msg, "error")
            print(error_msg)
        
    
    def process_audio_input(self, audio_data: Any, sample_rate: int) -> None:
        """Process audio input from user.
        
        Args:
            audio_data: The audio data to process
            sample_rate: The sample rate of the audio
        """
        if not self.audio_processor:
            self._send_feedback("Audio processor not set", "error")
            return
        
        # Store audio data reference for later use when STT completes
        self.current_audio_data = audio_data
        
        # In PySide6, it's better to use a simpler approach for 
        # handling signal connections - just disconnect all and reconnect
        # This avoids issues with the RuntimeWarning
        self.audio_processor.stt_completed.disconnect()  # Disconnect all slots
        
        # Connect to receive the result when ready
        self.audio_processor.stt_completed.connect(self._on_stt_completed)
            
        # Use audio processor to convert speech to text (runs asynchronously)
        self.audio_processor.process_audio_to_text(audio_data, sample_rate)
    
    def _on_stt_completed(self, text: str) -> None:
        """Handle completion of speech-to-text conversion.
        
        Args:
            text: The transcribed text
        """
        if not text:
            self._send_feedback("Failed to transcribe speech", "error")
            return
            
        # Ensure we preserve the audio processor's mute state
        # Store the current mute state before processing
        mute_state = False
        if self.audio_processor and hasattr(self.audio_processor, 'mute_enabled'):
            mute_state = self.audio_processor.mute_enabled
            # Store mute state as a property so we can restore it later
            self.saved_mute_state = mute_state
            
        # Generate a unique ID for this message
        self.current_message_id = str(id(text))
        
        # Emit the user's text for UI
        self.text_update.emit(f"{self.current_message_id}_user", text)
        
        # Process the text input
        self.process_user_input(text)

    def parse_citation(self, msg: Dict[str, str]|str) -> Dict[str, str] | None:
        if not msg:
            return None
        if 'title' in msg and 'href' in msg:
            # Handle dictionary format with title and href
            return({
                'format': 'websearch',
                'title': msg.get('title', 'N/A'),
                'href': msg.get('href', 'no URL')
            })
        elif 'pmid' in msg:
            #Handle pubmed tool format
            return({
                'format': 'pubmed',
                'pmid': msg.get('pmid', 'N/A'),
                'title': msg.get('title', 'N/A'),
                'authors': msg.get('authors', 'N/A'),
                'publication_date': msg.get('publication_date', 'N/A'),
                'journal': msg.get('journal', 'N/A'),
                'doi': msg.get('doi', 'N/A'),
                'abstract': msg.get('abstract', 'N/A')
            })
        elif isinstance(msg, str):
            # Handle string format (treat the string as both title and URL)
            return({
                'format': 'unknown',
                'title': msg,
                'href': msg
            })
        # Unrecognized format
        return None

    def get_citations(self, chunk: Any) -> List[Dict[str, str]]:
        """Extract citations from the chunk content.
        
        Args:
            chunk: The chunk of data to extract citations from
            
        Returns:
            List[Dict[str, str]]: A list of citation dictionaries with 'title' and 'href' keys
        """
        citations = []
        
        # Only process if chunk has messages
        if not hasattr(chunk, 'messages') or not chunk.messages:
            return citations
        
        # Find only tool messages that are part of the current run
        # We need to identify the current run's messages
        run_tool_messages = []
        
        # First, determine if this is a completed run with a final assistant message
        has_assistant_response = False
        for message in reversed(chunk.messages):
            if message.role == 'assistant':
                has_assistant_response = True
                break
                
        # If we have an assistant response, collect tool messages that came after
        # the previous assistant response (if any) and before the current one
        if has_assistant_response:
            collecting_tool_messages = False
            found_current_assistant = False
            
            for message in reversed(chunk.messages):
                # When we hit an assistant message, toggle our collector state
                if message.role == 'assistant':
                    if found_current_assistant:
                        # We've reached the previous assistant message, stop collecting
                        break
                    else:
                        # We've found the current assistant message (from reverse order)
                        found_current_assistant = True
                        collecting_tool_messages = True
                        continue
                
                # Collect tool messages between the last assistant message and current one
                if collecting_tool_messages and message.role == 'tool':
                    run_tool_messages.insert(0, message)  # Insert at beginning to maintain order
        
        # Process the tool messages for this run
        for tool_message in run_tool_messages:
            try:
                # Parse JSON content - check if content is already a list or needs parsing
                if isinstance(tool_message.content, list):
                    msglist = tool_message.content
                else:
                    msglist = json.loads(tool_message.content)
                
                # Add each citation for web search
                for msg in msglist:
                    citation = self.parse_citation(msg)
                    if citation:
                        citations.append(citation)
                    
            except json.JSONDecodeError:
                self._send_feedback("Error parsing tool message as JSON", "error")
                print("<ERROR>")
                pprint(tool_message)
                print("</ERROR>")
            except Exception as e:
                print(f"Error processing citations: {str(e)}")
                print("<ERROR>")
                pprint(tool_message)
                print("</ERROR>")
                self._send_feedback(f"Error processing citations: {str(e)}", "error")

        # If citations were found, format and append to message
        if citations:
            citationsstring = self.format_citations(citations)
            # Instead of sending as feedback, append to current message
            self._append_citations_to_message(citationsstring)
        return citations


    def format_citations(self, citations: List[Union[Dict[str, str], str]]) -> str:
        """Format citations into a readable string.
        
        Args:
            citations: List of citations, which can be either dictionaries with 'title' and 'href' keys,
                      or simple strings containing URLs
                      
        Returns:
            Formatted string with citations
        """
        citationstr = "<div class='references'>\n<h3>References</h3>\n<ol>"
        
        for citation in citations:
            if isinstance(citation, dict):
                # Handle dictionary format with title and href
                citation_type = citation.get('format', 'unknown')
                
                if citation_type == 'pubmed':
                    # Format PubMed citations in academic style
                    pmid = citation.get('pmid', None)
                    url = "https://pubmed.ncbi.nlm.nih.gov"
                    if pmid:
                        url = f"{url}/{pmid}/"
                    
                    authors = citation.get('authors', 'Unknown Authors')
                    if len(authors) > 50:
                        authors = f"{authors[:50]}..."
                    
                    pub_date = citation.get('publication_date', 'N/A')
                    title = citation.get('title', 'No title')
                    journal = citation.get('journal', '')
                    doi = citation.get('doi', '')
                    
                    citationstr += f"\n  <li>\n    <div class='citation academic'>\n"
                    citationstr += f"      <p>{authors} ({pub_date}). <a href='{url}'><strong>{title}</strong></a>."
                    
                    if journal:
                        citationstr += f" <em>{journal}</em>."
                    
                    if doi:
                        citationstr += f" DOI: {doi}"
                    
                    citationstr += "</p>\n    </div>\n  </li>"
                
                elif citation_type == 'websearch':
                    # Format web citations in a clean style
                    title = citation.get('title', 'N/A')
                    url = citation.get('href', '#')
                    
                    citationstr += f"\n  <li>\n    <div class='citation web'>\n"
                    citationstr += f"      <p><a href='{url}'>{title}</a></p>\n"
                    citationstr += f"      <p class='url'>{url}</p>\n"
                    citationstr += "    </div>\n  </li>"
                
                else:
                    # Handle unknown dictionary format
                    citationstr += f"\n  <li>\n    <div class='citation unknown'>\n"
                    citationstr += f"      <p>{str(citation)}</p>\n"
                    citationstr += "    </div>\n  </li>"
            
            elif isinstance(citation, str):
                # Handle string format (treat as URL)
                citationstr += f"\n  <li>\n    <div class='citation url-only'>\n"
                citationstr += f"      <p><a href='{citation}'>{citation}</a></p>\n"
                citationstr += "    </div>\n  </li>"
            
            else:
                # Handle unexpected format
                citationstr += f"\n  <li>\n    <div class='citation fallback'>\n"
                citationstr += "      <p>Unknown reference format</p>\n"
                citationstr += "    </div>\n  </li>"
        
        citationstr += "\n</ol>\n</div>\n\n<style>\n"
        citationstr += ".references { margin-top: 30px; border-top: 1px solid #e0e0e0; padding-top: 20px; }\n"
        citationstr += ".references h3 { font-size: 1.3rem; margin-bottom: 15px; }\n"
        citationstr += ".references ol { padding-left: 20px; }\n"
        citationstr += ".citation { margin-bottom: 12px; }\n"
        citationstr += ".citation a { color: inherit; text-decoration: underline; }\n"
        citationstr += ".citation a:hover { opacity: 0.8; }\n"
        citationstr += ".citation.academic p { line-height: 1.5; }\n"
        citationstr += ".citation.web .url { font-size: 0.85rem; color: #888; margin-top: 3px; }\n"
        citationstr += "</style>"
        
        return citationstr
    
                                
    def astream(self, prompt: str) -> Iterator[str]:
        """Stream responses from the LLM with absolute minimal latency.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            str: Chunks of the LLM's response
        """
        # Debug message moved to process_user_input to avoid duplication
        
        stream = self.agent.run(prompt, 
                                stream=True,
                                stream_intermediate_steps=True,
        )
        for chunk in stream:
            match(chunk.event):
                case 'RunCompleted':
                    self._send_feedback("Response complete", "debug")
                    self.get_citations(chunk)
                case 'RunResponse':
                    yield chunk.content
                case 'RunStarted':
                    pass
                    #self._send_feedback("Starting to generate response...", "info")
                case 'ToolCallStarted':
                    self._send_feedback(f"Using tool: {chunk.content}", "info")
                    self.audio_processor.tts(random_choice(RESEARCHING_FEEDBACKS))
                case 'ToolCallCompleted':
                    self._send_feedback(f"Tool call completed: {chunk.content}", "info")
                    self.audio_processor.tts(random_choice(RESEARCH_COMPLETED_FEEDBACKS))
                case 'UpdatingMemory':
                    self._send_feedback("Updating conversation memory...", "debug")
                case 'FinalResponse':
                    self._send_feedback("Response complete", "debug")
                case _:    
                    self._send_feedback(f"Unknown event: {chunk.event}", "debug")
                    
    async def astream_async(self, prompt: str) -> AsyncIterator[str]:
        """Asynchronously stream responses from the LLM with absolute minimal latency.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            str: Chunks of the LLM's response
        """
        # Debug message moved to process_user_input to avoid duplication
        
        stream = await self.agent.arun(prompt, 
                                      stream=True,
                                      stream_intermediate_steps=True,
        )
        async for chunk in stream:
            match(chunk.event):
                case 'RunCompleted':
                    self._send_feedback("Response complete", "debug")
                    self.get_citations(chunk)
                case 'RunResponse':
                    yield chunk.content
                case 'RunStarted':
                    pass
                    #self._send_feedback("Starting to generate response...", "info")
                case 'ToolCallStarted':
                    self._send_feedback(f"Using tool: {chunk.content}", "info")
                    if self.audio_processor:
                        self.audio_processor.tts(random_choice(RESEARCHING_FEEDBACKS))
                case 'ToolCallCompleted':
                    self._send_feedback(f"Tool call completed: {chunk.content}", "info")
                    if self.audio_processor:
                        self.audio_processor.tts(random_choice(RESEARCH_COMPLETED_FEEDBACKS))
                case 'UpdatingMemory':
                    self._send_feedback("Updating conversation memory...", "debug")
                case 'FinalResponse':
                    self._send_feedback("Response complete", "debug")
                case _:    
                    self._send_feedback(f"Unknown event: {chunk.event}", "debug")


           

                
    def get_model_name(self) -> str:
        """Get the current model name.
        
        Returns:
            str: The name of the LLM model being used
        """
        return self.model_name
    
    def set_model_name(self, model_name: str) -> None:
        """Set a new model name and update the agent model.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
        # Send feedback message about model change
        self._send_feedback(f"Changing model to: {self.model_name}", "info")
        
        # Update the agent's model to use the new model name
        try:
            self.agent.model = Ollama(id=self.model_name)
            self._send_feedback(f"Model successfully updated to: {self.model_name}", "info")
        except Exception as e:
            self._send_feedback(f"Error updating model: {str(e)}", "error")
    
    def _send_feedback(self, message: str, message_type: str = "info") -> None:
        """Send feedback messages via signal.
        
        Args:
            message: The message to send
            message_type: Type of message (info, debug, error)
        """
        # Emit signal for UI feedback
        self.feedback.emit(message, message_type)
        # Also print to console for debugging
        print(f"[{message_type.upper()}] {message}")
    
    def _on_chunk_received(self, chunk: str) -> None:
        """Handle receiving a chunk of the response.
        
        Args:
            chunk: A chunk of the response text
        """
        if not self.current_message_id:
            return
            
        # Add the chunk to the accumulated text
        self.assistant_text += chunk
        
        # Update the UI with the accumulated text using assistant message ID
        assistant_message_id = f"{self.current_message_id}_assistant"
        self.text_update.emit(assistant_message_id, self.assistant_text)
    
    def _on_processing_finished(self) -> None:
        """Handle completion of input processing."""
        # Emit signal to notify that processing is complete
        self.processing_complete.emit()
        
        # Also emit a signal to complete and save the assistant message
        # This ensures the message gets transferred from pending_messages to current_chat
        if hasattr(self, 'assistant_text') and self.current_message_id:
            assistant_message_id = f"{self.current_message_id}_assistant"
            # Re-emit the final text to ensure complete message is saved
            self.text_update.emit(assistant_message_id, self.assistant_text)
            # Send a special signal to mark completion
            self.feedback.emit(f"Assistant message {assistant_message_id} completed", "complete_message")
    
    def _process_sentence(self, sentence: str) -> None:
        """Process a complete sentence for TTS.
        
        Args:
            sentence: A complete sentence to process
        """
        if not self.audio_processor or not sentence.strip():
            return
            
        # CRITICAL FIX: Make sure we restore saved mute state before TTS processing
        # This ensures the mute checkbox setting is respected even after voice input
        if hasattr(self, 'saved_mute_state'):
            self.audio_processor.set_mute_state(self.saved_mute_state)
        
        # Force check mute state from AudioAssistant class if available
        # This ensures we're always respecting the current UI checkbox state
        try:
            # Walk up to find the AudioAssistant instance that owns this agent
            from rwb.audio.assistant import AudioAssistant
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, AudioAssistant) and hasattr(obj, 'mute_tts'):
                    self.saved_mute_state = obj.mute_tts
                    self.audio_processor.set_mute_state(obj.mute_tts)
                    break
        except Exception as e:
            print(f"Error finding AudioAssistant: {e}")
            
        # Final check of mute state before sending to TTS
            
        # Use the audio processor to convert text to speech
        self.audio_processor.tts(sentence.strip())
    
    def _append_citations_to_message(self, citations_text: str) -> None:
        """Append citations to the current assistant message.
        
        Args:
            citations_text: Formatted citation text to append
        """
        if not self.current_message_id:
            self._send_feedback("No active message to append citations to", "error")
            return
            
        # Append the citations to the current assistant text
        if hasattr(self, 'assistant_text'):
            # Append with a newline separator
            self.assistant_text = f"{self.assistant_text}\n\n{citations_text}"
            
            # Update the UI with the new text that includes citations
            # Use the correct assistant message ID format
            assistant_message_id = f"{self.current_message_id}_assistant"
            self.text_update.emit(assistant_message_id, self.assistant_text)
        else:
            # If there's no assistant_text attribute, log an error
            self._send_feedback("Failed to append citations: No assistant text found", "error")


if __name__ == "__main__":
    # agent = RWBAgent()
    # prompt = "What is happening in Germany today"
    # for chunk in agent.astream(prompt):
    #     # Print content if available
    #     print(chunk, end="")
    # print("\n--- End of Stream ---")

    import time
    import asyncio
    
    agent = RWBAgent()
    prompt = "What is happening in Germany today"
    
    # Test synchronous version
    print("Testing synchronous streaming...")
    start_time = time.time()
    first_chunk_time = None
    for i, chunk in enumerate(agent.astream(prompt)):
        if i == 0:
            first_chunk_time = time.time() - start_time
        print(chunk, end="")
    total_time = time.time() - start_time
    print(f"\nSync method - First chunk: {first_chunk_time:.3f}s, Total: {total_time:.3f}s")
    
    # Test asynchronous version
    print("\nTesting asynchronous streaming...")
    async def test_async():
        start_time = time.time()
        first_chunk_time = None
        i = 0
        async for chunk in await agent.astream_async(prompt):
            if i == 0:
                first_chunk_time = time.time() - start_time
                i += 1
            print(chunk, end="")
        total_time = time.time() - start_time
        print(f"\nAsync method - First chunk: {first_chunk_time:.3f}s, Total: {total_time:.3f}s")
    
    asyncio.run(test_async())