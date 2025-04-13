"""Agent module.

This module provides the RWBAgent class for handling LLM inference
and streaming responses, separate from audio processing.
"""
import os
import pathlib
from typing import Iterator, List, Dict, Any, Optional, Union
import asyncio
from textwrap import dedent
from datetime import datetime
import json
from pprint import pprint
from dotenv import load_dotenv

from PySide6.QtCore import QObject, Signal, QMutex, QThreadPool

# Import the sentence splitter at module level
from rwb.audio.processor import split_into_sentences
from rwb.agents.worker import InputProcessorWorker

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools
#from agno.tools.pubmed import PubmedTools. #it sucks
from rwb.tools.pubmed import PubMedTools
from agno.tools.python import PythonTools
from agno.tools.wikipedia import WikipediaTools


#MODEL= "phi4:latest"
#MODEL="mistral-small3.1"
MODEL = "qwen2.5:14b-instruct-q8_0"
#MODEL= "granite3.2:8b-instruct-q8_0"
# Load environment variables from .env file
load_dotenv()
AUTHOR_EMAIL = os.getenv("AUTHOR_EMAIL") or "default@example.com"
print(f"Author email: {AUTHOR_EMAIL}")

PYTHONTOOLS_BASEDIR = pathlib.Path("~/.rwbtmp/python") 
if not PYTHONTOOLS_BASEDIR.exists():
    os.makedirs(PYTHONTOOLS_BASEDIR, exist_ok=True)


class RWBAgent(QObject):
    """Handles LLM inference and streaming responses."""
    
    # Define signals
    feedback = Signal(str, str)  # Signal for feedback messages (message, message_type)
    text_update = Signal(str, str)  # Signal for text updates (message_id, text)
    processing_complete = Signal()  # Signal for when processing is complete
    
    def __init__(self, model_name: str = MODEL):
        """Initialize the agent.
        
        Args:
            model_name: Name of the LLM model to use
        """
        super().__init__()
        self.model_name = model_name
        self.audio_processor = None  # Will be set later
        self.current_message_id = None
        
        # Send feedback message
        self._send_feedback(f"Initializing RWBAgent with model: {self.model_name}", "info")
        
        self.agent = Agent(
            model=Ollama(id=self.model_name),
            add_history_to_messages=True,
            # Number of historical responses to add to the messages.
            num_history_responses=5,
            read_chat_history=True,
            tools=[DuckDuckGoTools(), 
                   PubMedTools(email=AUTHOR_EMAIL, max_results=20), 
                   WikipediaTools(), 
                   PythonTools(base_dir=PYTHONTOOLS_BASEDIR)],
            instructions=dedent(f"""Your name is Emily. Today's actual date is {datetime.now().strftime('%Y-%m-%d')}.
            I am Dr Horst Herb, a German physician living in Australia. You may address me as Horst
            You are a helpful research assistant able to choose and use tools when appropriate.
            If you are not confident that you can answer the user with confidence, select the most appropriate tool
            to answer. Be concise in your answer.
            After using a tool, always provide a helpful response based on the tool's output."""),
            show_tool_calls=True,
            markdown=True,
        )
    
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
            
        # Generate a unique ID for this message
        self.current_message_id = str(id(text))
        
        # Emit the user's text for UI
        self.text_update.emit(f"{self.current_message_id}_user", text)
        
        # Process the text input
        self.process_user_input(text)

    def parse_citation(self, msg: Dict[str, str]|str) -> Dict[str, str]:
        if not msg:
            return []
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
        elif type(msg) == str:
            # Handle string format (treat the string as both title and URL)
            return({
                'format': 'unknown',
                'title': msg,
                'href': msg
            })


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
            
        # Get only the last 'tool' message - traverse from last to first
        last_tool_message = None
        for message in reversed(chunk.messages):
            if message.role == 'tool':
                last_tool_message = message
                break
                
        # Process only the last tool message if found
        if last_tool_message:
            try:
                # Parse JSON content - check if content is already a list or needs parsing
                if isinstance(last_tool_message.content, list):
                    msglist = last_tool_message.content
                else:
                    msglist = json.loads(last_tool_message.content)
                
                # Add each citation for web search
                for msg in msglist:
                    citation = self.parse_citation(msg)
                    if citation:
                        citations.append(citation)
                    
            except json.JSONDecodeError:
                self._send_feedback("Error parsing tool message as JSON", "error")
                pprint(chunk)
            except Exception as e:
                print(f"Error processing citations: {str(e)}")
                pprint(chunk)
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
        from typing import Union
        
        citationstr = "### References:<br>"
        for n, citation in enumerate(citations):
            if isinstance(citation, dict):
                # Handle dictionary format with title and href
                citation_type = citation.get('format', 'unknown')
                if citation_type == 'pubmed':
                    pmid = citation.get('pmid', None)
                    urlstr="""https://pubmed.ncbi.nlm.nih.gov"""
                    if pmid:
                        urlstr = f"""{urlstr}/{pmid}/"""
                    citationstr += f"""- [{n+1}. PMID: {citation.get('pmid', 'N/A')} {citation.get('title', 'no title')}]({urlstr}) <br><small><i>Athors: {citation.get('authors', 'authors unknow')[:50]}...</i></small><br><br>"""
                elif citation_type == 'websearch':
                    # Handle web search format
                    citationstr += f"{n+1}. [{citation.get('title', 'N/A')}]({citation.get('href', 'no URL')}) <small><i>({citation.get('href', 'no URL')})</i></small><br>"
                else:
                    # Handle unknown format
                    citationstr += f"{n+1}. {str(citation)}<br>"
            elif isinstance(citation, str):
                # Handle string format (treat the string as both title and URL)
                citationstr += f"{n+1}. [{citation}]({citation}) <small><i>({citation})</i></small><br>"
            else:
                # Handle unexpected format
                citationstr += f"{n+1}. Unknown reference format<br>"
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
                case 'ToolCallCompleted':
                    self._send_feedback(f"Tool call completed: {chunk.content}", "info")
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
        """Set a new model name.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name 
    
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
    agent = RWBAgent()
    prompt = "What is happening in Germany today"
    for chunk in agent.astream(prompt):
        # Print content if available
        print(chunk, end="")
    print("\n--- End of Stream ---")