# RWB API Reference

This document provides detailed API documentation for all modules in the Researcher's Workbench (RWB) project.

## Table of Contents

1. [Core Modules](#core-modules)
   - [rwb.context](#rwbcontext)
   - [rwb.\_\_main\_\_](#rwb__main__)
2. [Agent Modules](#agent-modules)
   - [rwb.agents.rwbagent](#rwbagentsrwbagent)
   - [rwb.agents.worker](#rwbagentsworker)
3. [Audio Modules](#audio-modules)
   - [rwb.audio.assistant](#rwbaudioassistant)
   - [rwb.audio.processor](#rwbaudioprocessor)
   - [rwb.audio.recorder](#rwbaudiorecorder)
   - [rwb.audio.chat_message](#rwbaudiochat_message)
   - [rwb.audio.chat_history](#rwbaudiochat_history)
4. [UI Modules](#ui-modules)
   - [rwb.audio.ui.components](#rwbaudiouicomponents)
   - [rwb.audio.ui.styles](#rwbaudiouistyles)
   - [rwb.audio.ui.settings_dialog](#rwbaudiouisettings_dialog)
   - [rwb.audio.ui.history_list](#rwbaudiouihistory_list)
5. [Helper Modules](#helper-modules)
   - [rwb.helpers.texts](#rwbhelperstexts)
   - [rwb.helpers.textsanitizer](#rwbhelperstextsanitizer)
6. [Tool Modules](#tool-modules)
   - [rwb.tools.pubmed_tools](#rwbtoolspubmed_tools)
   - [rwb.tools.pubmed](#rwbtoolspubmed)
7. [Platform Modules](#platform-modules)
   - [rwb.qt.plugin_manager](#rwbqtplugin_manager)
   - [rwb.llm.ollamamodels](#rwbllmollamamodels)

---

## Core Modules

### rwb.context

Configuration and settings management module.

#### Classes

##### `User`

Represents user information.

```python
class User:
    def __init__(
        self,
        title: str = "",
        firstname: str = "",
        surname: str = "",
        email: str = "",
        background: str = ""
    ):
        """
        Initialize a user.

        Args:
            title: User's title (Dr., Prof., etc.)
            firstname: User's first name
            surname: User's last name
            email: User's email address
            background: Brief description of user's background
        """
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, str]` | Convert user to dictionary |
| `from_dict(data)` | `User` | Create User from dictionary (classmethod) |

**Example:**
```python
user = User(
    title="Dr.",
    firstname="Jane",
    surname="Smith",
    email="jane@example.com",
    background="Biomedical researcher"
)
data = user.to_dict()
restored = User.from_dict(data)
```

---

##### `Assistant`

Represents assistant settings and personality.

```python
class Assistant:
    def __init__(
        self,
        name: str = "Emily",
        background: str = "I am an AI research assistant.",
        base_prompt: str = ""
    ):
        """
        Initialize assistant settings.

        Args:
            name: Assistant's name
            background: Assistant's background/persona description
            base_prompt: Base system prompt for all interactions
        """
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict[str, str]` | Convert assistant to dictionary |
| `from_dict(data)` | `Assistant` | Create Assistant from dictionary (classmethod) |

---

##### `ContextManager`

Singleton managing persistent user and assistant settings.

```python
class ContextManager:
    def __init__(self):
        """
        Initialize the context manager.
        Automatically loads settings on initialization.
        """
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `user` | `User` | Current user settings |
| `assistant` | `Assistant` | Current assistant settings |
| `model_name` | `str` | Selected LLM model name |
| `tts_voice` | `str` | Selected TTS voice |

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `load_settings()` | None | None | Load settings from storage |
| `save_user(user)` | `User` | None | Save user settings |
| `save_assistant(assistant)` | `Assistant` | None | Save assistant settings |

**Singleton Access:**
```python
from rwb.context import context_manager

# Read
user = context_manager.user
model = context_manager.model_name

# Write
context_manager.model_name = "new-model"
context_manager.save_user(new_user)
```

---

### rwb.\_\_main\_\_

Application entry point module.

#### Functions

##### `main()`

```python
def main() -> None:
    """
    Main entry point for the application.

    Initializes the Qt application, sets up the plugin manager,
    and starts the main window.
    """
```

**Usage:**
```bash
python -m rwb
```

---

## Agent Modules

### rwb.agents.rwbagent

LLM agent handling inference and tool usage.

#### Classes

##### `RWBAgent`

Main agent class for LLM inference. Inherits from `QObject`.

```python
class RWBAgent(QObject):
    # Signals
    feedback = Signal(str, str)       # (message, type)
    text_update = Signal(str, str)    # (message_id, text)
    processing_complete = Signal()     # Completion notification

    def __init__(self, model_name: str = None):
        """
        Initialize the RWBAgent.

        Args:
            model_name: The name of the LLM model to use (optional).
                       Defaults to "mistral-small3.1" if not provided.
        """
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `set_audio_processor(processor)` | `AudioProcessor` | None | Set the audio processor for TTS |
| `process_user_input(input_text)` | `str` | None | Process text input (async) |
| `process_audio_input(audio_data, sample_rate)` | `Any, int` | None | Process audio input |
| `astream(prompt)` | `str` | `Iterator[str]` | Stream LLM responses |
| `astream_async(prompt)` | `str` | `AsyncIterator[str]` | Async stream LLM responses |
| `get_model_name()` | None | `str` | Get current model name |
| `set_model_name(model_name)` | `str` | None | Change LLM model |
| `get_user()` | None | `User` | Get user from context manager |
| `get_citations(chunk)` | `Any` | `List[Dict]` | Extract citations from response |
| `format_citations(citations)` | `List` | `str` | Format citations as HTML |

**Signal Descriptions:**

- `feedback(message: str, type: str)`: Emits status messages
  - Types: `"info"`, `"debug"`, `"error"`, `"complete_message"`

- `text_update(message_id: str, text: str)`: Emits text updates
  - `message_id` format: `{id}_user` or `{id}_assistant`

- `processing_complete()`: Emits when processing finishes

**Example:**
```python
agent = RWBAgent(model_name="qwen2.5:14b-instruct-q8_0")
agent.set_audio_processor(processor)

# Connect signals
agent.text_update.connect(on_text_update)
agent.feedback.connect(on_feedback)

# Process input
agent.process_user_input("What is machine learning?")
```

---

### rwb.agents.worker

Background worker classes for async processing.

#### Classes

##### `WorkerSignals`

Signal definitions for workers.

```python
class WorkerSignals(QObject):
    chunk = Signal(str)           # Text chunk received
    sentence_ready = Signal(str)  # Complete sentence for TTS
    finished = Signal()           # Processing complete
    error = Signal(str)           # Error occurred
```

##### `InputProcessorWorker`

Processes user input in a background thread.

```python
class InputProcessorWorker(QRunnable):
    def __init__(self, agent_stream, input_text: str):
        """
        Initialize the worker.

        Args:
            agent_stream: Generator function for streaming responses
            input_text: User input text to process
        """
```

**Methods:**

| Method | Description |
|--------|-------------|
| `run()` | Execute the worker (called by thread pool) |

---

## Audio Modules

### rwb.audio.assistant

Main GUI application window.

#### Classes

##### `AudioAssistant`

Main window for the voice assistant. Inherits from `QMainWindow`.

```python
class AudioAssistant(QMainWindow):
    def __init__(self) -> None:
        """
        Initialize the AudioAssistant.

        Sets up:
        - Window settings and geometry
        - Tabbed UI (Chat, History)
        - RWBAgent for LLM inference
        - AudioRecorder for microphone input
        - STT/TTS models
        - AudioProcessor for audio handling
        - Signal connections
        """
```

**Key Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `agent` | `RWBAgent` | LLM agent instance |
| `processor` | `AudioProcessor` | Audio processing instance |
| `recorder` | `AudioRecorder` | Audio recording instance |
| `chat_history` | `ChatHistory` | Chat persistence |
| `settings` | `QSettings` | Application settings |
| `current_messages` | `Dict[str, ChatMessage]` | Active chat messages |
| `mute_tts` | `bool` | TTS mute state |

**Methods:**

| Method | Description |
|--------|-------------|
| `setup_tabbed_ui()` | Set up the tabbed interface |
| `setup_chat_ui()` | Set up the chat tab |
| `setup_history_ui()` | Set up the history tab |
| `start_recording()` | Start audio recording |
| `stop_recording()` | Stop recording and process |
| `stop_processing()` | Cancel ongoing processing |
| `send_text()` | Send text input to agent |
| `open_settings_dialog()` | Open settings dialog |
| `shutdown()` | Clean up and close |

**Slots:**

| Slot | Parameters | Description |
|------|------------|-------------|
| `handle_text_update` | `str, str` | Handle streaming text |
| `handle_feedback` | `str, str` | Handle status messages |
| `handle_speaking_started` | None | TTS started |
| `handle_speaking_ended` | None | TTS finished |
| `handle_processing_error` | `str` | Error occurred |
| `handle_stt_completed` | `str` | STT finished |
| `toggle_mute` | `int` | Toggle TTS muting |

---

### rwb.audio.processor

Audio processing for STT and TTS.

#### Classes

##### `AudioProcessor`

Handles all audio operations. Inherits from `QObject`.

```python
class AudioProcessor(QObject):
    # Signals
    speaking = Signal()          # TTS playback started
    done_speaking = Signal()     # TTS playback finished
    stt_completed = Signal(str)  # STT transcription done
    error = Signal(str)          # Error occurred

    def __init__(
        self,
        stt_model,
        tts_model,
        tts_options
    ):
        """
        Initialize the AudioProcessor.

        Args:
            stt_model: Speech-to-text model instance
            tts_model: Text-to-speech model instance
            tts_options: TTS configuration options
        """
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `tts(text)` | `str` | None | Queue text for TTS |
| `process_audio_to_text(audio_data, sample_rate)` | `Any, int` | None | Queue audio for STT |
| `set_mute_state(muted)` | `bool` | None | Set TTS mute state |
| `cancel_processing()` | None | None | Cancel all operations |
| `reset_cancellation_flag()` | None | None | Reset cancel flag |
| `clear_tts_queue()` | None | None | Clear pending TTS |
| `stop_tts_queue_processor()` | None | None | Stop TTS thread |
| `disconnect_signals()` | None | None | Disconnect all signals |
| `cleanup()` | None | None | Clean up resources |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_speaking` | `bool` | Whether TTS is playing |
| `mute_enabled` | `bool` | Whether TTS is muted |

#### Functions

##### `split_into_sentences(text)`

```python
def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences for TTS processing.

    Args:
        text: Input text to split

    Returns:
        List of sentences
    """
```

---

### rwb.audio.recorder

Audio recording functionality.

#### Classes

##### `AudioRecorder`

Manages microphone input.

```python
class AudioRecorder:
    RATE = 44100        # Sample rate
    CHANNELS = 1        # Mono
    FORMAT = pyaudio.paFloat32
    CHUNK = 1024        # Buffer size

    def __init__(self):
        """Initialize the audio recorder."""
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `start_recording()` | None | Begin recording |
| `stop_recording()` | `np.ndarray` | Stop and return audio data |
| `cleanup()` | None | Release resources |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `recording` | `bool` | Whether currently recording |

---

### rwb.audio.chat_message

Chat message widget.

#### Enums

##### `MessageSender`

```python
class MessageSender(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    OTHER = "other"
```

#### Classes

##### `ChatMessage`

Visual representation of a chat message. Inherits from `QFrame`.

```python
class ChatMessage(QFrame):
    def __init__(
        self,
        text: str,
        sender: MessageSender,
        parent=None
    ):
        """
        Initialize a chat message widget.

        Args:
            text: Message text (supports markdown)
            sender: Message sender type
            parent: Parent widget
        """
```

**Methods:**

| Method | Parameters | Description |
|--------|------------|-------------|
| `update_text(text)` | `str` | Update message content |

---

### rwb.audio.chat_history

Chat history persistence.

#### Classes

##### `ChatHistory`

Manages saving and loading chat history.

```python
class ChatHistory:
    def __init__(self):
        """
        Initialize chat history manager.

        Creates storage directory at ~/.rwb/chat_history/
        """
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add_message(text, sender, message_id)` | `str, MessageSender, str` | None | Add message |
| `complete_message(message_id)` | `str` | None | Mark complete |
| `save()` | None | None | Save to disk |
| `get_history_files()` | None | `List[str]` | List history files |

**Storage Format:**
```json
[
  {
    "text": "message content",
    "sender": "user|assistant|system",
    "timestamp": "ISO-8601",
    "format": "markdown"
  }
]
```

---

## UI Modules

### rwb.audio.ui.components

Reusable UI component factory functions.

#### Functions

```python
def create_status_label() -> QLabel:
    """Create the status label widget."""

def create_talk_button() -> QPushButton:
    """Create the talk/record button."""

def create_stop_button() -> QPushButton:
    """Create the stop button."""

def create_mute_button() -> QPushButton:
    """Create the mute voice output button."""

def create_text_input() -> QTextEdit:
    """Create the text input widget."""

def create_send_button() -> QPushButton:
    """Create the send button."""

def create_chat_scroll_area() -> Tuple[QScrollArea, QWidget, QVBoxLayout]:
    """
    Create chat scroll area.

    Returns:
        Tuple of (scroll_area, container, layout)
    """

def create_button_layout() -> QHBoxLayout:
    """Create the button layout."""
```

---

### rwb.audio.ui.styles

Centralized styling constants.

#### Constants

**Status Messages:**
```python
STATUS_READY = "Ready to record"
STATUS_LISTENING = "Listening..."
STATUS_PROCESSING = "Processing..."
STATUS_SPEAKING = "Speaking..."
STATUS_STOPPED = "Stopped"
```

**Button Labels:**
```python
BUTTON_TALK = "Talk"
BUTTON_RECORDING = "Recording..."
BUTTON_PROCESSING = "Processing..."
```

**Stylesheets:**
```python
BUTTON_STYLE_RECORDING  # Recording state style
SETTINGS_BUTTON_STYLE   # Settings button style
TAB_WIDGET_STYLE        # Tab widget style
SPLITTER_STYLE          # Splitter style
TOOLTIP_STYLE           # Global tooltip style
```

---

### rwb.audio.ui.settings_dialog

Settings configuration dialog.

#### Classes

##### `SettingsDialog`

Modal dialog for application settings. Inherits from `QDialog`.

```python
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        """
        Initialize the settings dialog.

        Creates tabs for:
        - User settings
        - Assistant settings
        - Model settings
        """
```

**Tabs:**
- **User Tab**: Title, name, email, background
- **Assistant Tab**: Name, background, base prompt
- **Model Tab**: LLM model selection, TTS voice selection

---

### rwb.audio.ui.history_list

Chat history browser widget.

#### Classes

##### `HistoryList`

List widget for browsing chat history. Inherits from `QWidget`.

```python
class HistoryList(QWidget):
    # Signals
    history_selected = Signal(str)  # File path selected
    history_deleted = Signal(str)   # File path deleted

    def __init__(self, parent=None):
        """Initialize the history list widget."""
```

**Methods:**

| Method | Description |
|--------|-------------|
| `_load_histories()` | Refresh the history list |

---

## Helper Modules

### rwb.helpers.texts

Greeting and shutdown message generation.

#### Functions

```python
def random_greeting(user: User) -> str:
    """
    Generate a random greeting message.

    Args:
        user: User object for personalization

    Returns:
        Greeting message string
    """

def random_shutdown(user: User) -> str:
    """
    Generate a random shutdown message.

    Args:
        user: User object for personalization

    Returns:
        Shutdown message string
    """
```

---

### rwb.helpers.textsanitizer

Text sanitization for TTS.

#### Functions

##### `markdown_to_speech(text)`

```python
def markdown_to_speech(text: str) -> str:
    """
    Convert markdown text to TTS-friendly plain text.

    Transformations:
    - Removes markdown formatting (headers, bold, italic)
    - Replaces links with "link provided"
    - Replaces images with "image provided"
    - Removes code blocks
    - Expands common abbreviations
    - Handles medical terminology
    - Splits acronyms for pronunciation

    Args:
        text: Markdown-formatted text

    Returns:
        Plain text suitable for TTS
    """
```

**Example:**
```python
text = "Check this [article](http://example.com) about **ML**"
result = markdown_to_speech(text)
# Result: "Check this link provided about M L"
```

---

## Tool Modules

### rwb.tools.pubmed_tools

PubMed search toolkit for the agent.

#### Classes

##### `PubMedTools`

Toolkit for PubMed searches. Inherits from `Toolkit`.

```python
class PubMedTools(Toolkit):
    def __init__(
        self,
        email: str,
        max_results: int = 10
    ):
        """
        Initialize PubMed tools.

        Args:
            email: Email for NCBI Entrez identification
            max_results: Maximum results per search
        """
```

**Registered Methods:**

```python
def generate_pubmed_query(human_language: str) -> str:
    """
    Convert natural language to PubMed query syntax.

    Args:
        human_language: Natural language search query

    Returns:
        PubMed query string with proper syntax
    """

def search_pubmed(query: str, max_results: int = None) -> str:
    """
    Execute PubMed search.

    Args:
        query: PubMed query string
        max_results: Override default max results

    Returns:
        JSON string with search results
    """

def NL_pubmed_search(query: str) -> str:
    """
    Natural language PubMed search.

    Combines query generation and search execution.
    """
```

**Result Format:**
```json
[
  {
    "pmid": "12345678",
    "title": "Article Title",
    "authors": "Author A, Author B",
    "abstract": "Abstract text...",
    "journal": "Journal Name",
    "publication_date": "2025",
    "doi": "10.1234/example"
  }
]
```

---

### rwb.tools.pubmed

Advanced PubMed search implementation.

#### Functions

```python
def search_pubmed(
    query: str,
    email: str,
    max_results: int = 10
) -> List[Dict]:
    """
    Search PubMed using Entrez API.

    Args:
        query: PubMed query string
        email: Email for API identification
        max_results: Maximum results to return

    Returns:
        List of article dictionaries
    """

def format_pubmed_results(results: List[Dict]) -> str:
    """
    Format PubMed results for display.

    Args:
        results: List of article dictionaries

    Returns:
        Formatted string representation
    """
```

---

## Platform Modules

### rwb.qt.plugin_manager

Qt plugin management (critical for macOS).

#### Classes

##### `QtPluginManager`

Manages Qt platform plugins discovery and configuration.

```python
class QtPluginManager:
    def __init__(self):
        """Initialize the Qt plugin manager."""

    def setup_plugins(self) -> bool:
        """
        Set up Qt plugins.

        Searches for Qt plugins in:
        1. Cached path
        2. Virtual environment
        3. PySide6 installation
        4. System site-packages
        5. User home directory

        Returns:
            True if plugins found and configured, False otherwise
        """

    def verify_plugins(self) -> bool:
        """
        Verify that Qt plugins are working.

        Returns:
            True if plugins are functional
        """
```

**Usage:**
```python
plugin_manager = QtPluginManager()
if not plugin_manager.setup_plugins():
    print("Qt plugins not found!")
    sys.exit(1)
```

---

### rwb.llm.ollamamodels

Ollama model utilities.

#### Functions

```python
def get_available_models() -> List[str]:
    """
    Get list of available Ollama models.

    Returns:
        List of model names available on local Ollama server
    """

def is_model_available(model_name: str) -> bool:
    """
    Check if a specific model is available.

    Args:
        model_name: Name of the model to check

    Returns:
        True if model is available
    """
```

---

## Type Definitions

### Common Types

```python
from typing import Dict, List, Any, Optional, Iterator, AsyncIterator
from PySide6.QtCore import Signal

# Message ID format
MessageId = str  # Format: "{unique_id}_user" or "{unique_id}_assistant"

# Chat message format
ChatMessageData = Dict[str, Any]
# {
#     "text": str,
#     "sender": "user"|"assistant"|"system",
#     "timestamp": str,
#     "format": "markdown"
# }

# Citation format
Citation = Dict[str, str]
# {
#     "format": "pubmed"|"websearch"|"unknown",
#     "title": str,
#     "href": str,
#     ...
# }
```

---

## Error Handling

### Common Exceptions

Most modules handle exceptions internally and emit error signals or print to console:

```python
# Agent errors
agent.feedback.emit("Error message", "error")

# Processor errors
processor.error.emit("Error message")

# Common patterns
try:
    # Operation
except Exception as e:
    self._send_feedback(f"Error: {str(e)}", "error")
    print(f"[ERROR] {str(e)}")
```

### Recommended Error Handling

```python
# Connect to error signals
processor.error.connect(handle_error)
agent.feedback.connect(handle_feedback)

def handle_error(message: str):
    print(f"Audio error: {message}")

def handle_feedback(message: str, msg_type: str):
    if msg_type == "error":
        print(f"Agent error: {message}")
```
