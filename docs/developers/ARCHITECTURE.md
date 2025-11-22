# RWB Architecture Guide

This document provides a comprehensive overview of the Researcher's Workbench (RWB) architecture, design patterns, and system interactions.

## System Overview

RWB is a Qt-based voice assistant application designed for biomedical research. It combines:

- **Local LLM inference** via Ollama
- **Speech-to-Text (STT)** using Whisper via fastrtc
- **Text-to-Speech (TTS)** using Kokoro via fastrtc
- **Agentic capabilities** with research tools (PubMed, DuckDuckGo, Wikipedia)
- **Persistent chat history** and user preferences

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AudioAssistant                                │
│                        (Main Window - QMainWindow)                      │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────────┐ │
│  │  Chat Tab    │  │  History Tab  │  │    Settings Dialog           │ │
│  │              │  │               │  │                              │ │
│  │ - Input area │  │ - File list   │  │ - User profile               │ │
│  │ - Messages   │  │ - Chat viewer │  │ - Assistant settings         │ │
│  │ - Controls   │  │               │  │ - Model selection            │ │
│  └──────────────┘  └───────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│    AudioRecorder    │              │   ContextManager    │
│  - Microphone input │              │  - User settings    │
│  - Audio capture    │              │  - Assistant config │
└─────────────────────┘              │  - Model prefs      │
         │                           └─────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           RWBAgent                                      │
│                      (Agent - QObject)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Agno Agent      │  │  Tools           │  │  Audio Processor     │  │
│  │  - Ollama LLM    │  │  - DuckDuckGo    │  │  - STT (Whisper)     │  │
│  │  - Streaming     │  │  - PubMed        │  │  - TTS (Kokoro)      │  │
│  │  - History       │  │  - Wikipedia     │  │  - Queue management  │  │
│  │                  │  │  - Website       │  │                      │  │
│  │                  │  │  - Python        │  │                      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│    ChatHistory      │              │  External Services  │
│  - JSON storage     │              │  - Ollama server    │
│  - ~/.rwb/chat_*    │              │  - NCBI Entrez      │
└─────────────────────┘              │  - Web APIs         │
                                     └─────────────────────┘
```

## Component Details

### 1. Main Application (`rwb/__main__.py`)

The entry point initializes the Qt application:

```python
def main() -> None:
    # 1. Setup Qt plugins (critical for macOS)
    plugin_manager = QtPluginManager()
    plugin_manager.setup_plugins()

    # 2. Create Qt application
    app = QApplication(sys.argv)

    # 3. Create and show main window
    window = AudioAssistant()
    window.show()

    # 4. Start event loop
    sys.exit(app.exec())
```

### 2. AudioAssistant (`rwb/audio/assistant.py`)

The main window class managing all UI and coordination:

**Responsibilities:**
- Window management (size, position persistence)
- Tab interface (Chat, History)
- User input handling (voice button, text input)
- Signal routing between components
- Lifecycle management (startup, shutdown)

**Key Attributes:**
```python
self.agent          # RWBAgent - LLM inference
self.processor      # AudioProcessor - STT/TTS
self.recorder       # AudioRecorder - Microphone
self.chat_history   # ChatHistory - Persistence
self.settings       # QSettings - Preferences
```

**Signal Connections:**
```python
# Audio processor signals
processor.speaking.connect(handle_speaking_started)
processor.done_speaking.connect(handle_speaking_ended)
processor.stt_completed.connect(handle_stt_completed)
processor.error.connect(handle_processing_error)

# Agent signals
agent.feedback.connect(handle_feedback)
agent.text_update.connect(handle_text_update)
```

### 3. RWBAgent (`rwb/agents/rwbagent.py`)

The LLM agent handling inference and tool usage:

**Initialization:**
```python
self.agent = Agent(
    model=Ollama(id=self.model_name),
    add_history_to_messages=True,
    num_history_responses=5,
    tools=[
        DuckDuckGoTools(),
        WebsiteTools(),
        PubMedTools(email=..., max_results=20),
        WikipediaTools(),
        PythonTools(base_dir=...)
    ],
    instructions=self._build_instructions(),
    show_tool_calls=True,
    markdown=True,
)
```

**Signal Definitions:**
```python
feedback = Signal(str, str)        # (message, type)
text_update = Signal(str, str)     # (message_id, text)
processing_complete = Signal()      # Completion notification
```

**Processing Flow:**
```
User Input → process_user_input() → InputProcessorWorker
                                            │
                                            ▼
                                    astream() generator
                                            │
                                            ▼
                                    Chunk events:
                                    - RunResponse → text_update signal
                                    - ToolCallStarted → feedback + TTS
                                    - ToolCallCompleted → feedback + TTS
                                    - RunCompleted → citations
```

### 4. AudioProcessor (`rwb/audio/processor.py`)

Thread-safe audio processing for STT and TTS:

**Key Features:**
- Queue-based TTS processing (one sentence at a time)
- Thread pool for background STT processing
- PyAudio for audio I/O
- Librosa for audio resampling

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    AudioProcessor                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐        ┌─────────────────────┐    │
│  │   STT Model     │        │   TTS Model         │    │
│  │   (Whisper)     │        │   (Kokoro)          │    │
│  └────────┬────────┘        └──────────┬──────────┘    │
│           │                            │               │
│           ▼                            ▼               │
│  ┌─────────────────┐        ┌─────────────────────┐    │
│  │  ThreadPool     │        │   TTS Queue         │    │
│  │  Worker         │        │   (thread-safe)     │    │
│  └────────┬────────┘        └──────────┬──────────┘    │
│           │                            │               │
│           ▼                            ▼               │
│  ┌─────────────────┐        ┌─────────────────────┐    │
│  │ stt_completed   │        │   Audio Playback    │    │
│  │ signal          │        │   (PyAudio)         │    │
│  └─────────────────┘        └─────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**TTS Queue Processing:**
```python
def _process_tts_queue(self):
    """Background thread processing TTS queue."""
    while self._tts_queue_running:
        try:
            text = self._tts_queue.get(timeout=0.1)
            if text is None:  # Shutdown signal
                break
            self._process_tts_text_sync(text)
        except queue.Empty:
            continue
```

### 5. ContextManager (`rwb/context.py`)

Singleton managing persistent settings:

**Data Classes:**
```python
class User:
    title: str      # Dr., Prof., etc.
    firstname: str
    surname: str
    email: str
    background: str

class Assistant:
    name: str           # Assistant name
    background: str     # Persona description
    base_prompt: str    # Custom system prompt
```

**Storage:**
```python
# Uses QSettings for platform-native storage
self.settings = QSettings("RWB", "ResearchWithoutBorders")

# Settings stored:
# - user (JSON)
# - assistant (JSON)
# - model/name
# - tts/voice
```

**Access Pattern:**
```python
from rwb.context import context_manager

# Read settings
user = context_manager.user
model = context_manager.model_name

# Write settings
context_manager.model_name = "new-model"
context_manager.save_user(user)
```

### 6. ChatHistory (`rwb/audio/chat_history.py`)

Manages conversation persistence:

**Storage Location:** `~/.rwb/chat_history/`

**File Format:**
```json
[
  {
    "text": "User message text",
    "sender": "user",
    "timestamp": "2025-11-22T12:34:56.123456",
    "format": "markdown"
  },
  {
    "text": "Assistant response in **markdown**",
    "sender": "assistant",
    "timestamp": "2025-11-22T12:35:10.789012",
    "format": "markdown"
  }
]
```

**Key Methods:**
```python
add_message(text, sender, message_id)  # Add message
complete_message(message_id)            # Mark as complete
save()                                  # Write to disk
```

### 7. Worker Classes (`rwb/agents/worker.py`)

Background processing using Qt's thread pool:

**InputProcessorWorker:**
```python
class InputProcessorWorker(QRunnable):
    """Processes user input in background thread."""

    class Signals(QObject):
        chunk = Signal(str)          # Text chunk received
        sentence_ready = Signal(str) # Complete sentence for TTS
        finished = Signal()          # Processing complete
        error = Signal(str)          # Error occurred

    def run(self):
        for chunk in self.agent_stream(self.input_text):
            self.signals.chunk.emit(chunk)
            # Split into sentences
            sentences = split_into_sentences(chunk)
            for sentence in sentences:
                self.signals.sentence_ready.emit(sentence)
        self.signals.finished.emit()
```

## Data Flow Diagrams

### Voice Input Flow

```
User presses "Talk" button
         │
         ▼
AudioRecorder.start_recording()
         │
         ▼
Timer captures audio chunks → numpy array
         │
         ▼
User releases button
         │
         ▼
AudioRecorder.stop_recording() → audio_data
         │
         ▼
RWBAgent.process_audio_input(audio_data, sample_rate)
         │
         ▼
AudioProcessor.process_audio_to_text()
         │
         ▼
STT Worker Thread
         │
         ▼
Whisper Model → transcribed text
         │
         ▼
stt_completed signal
         │
         ▼
RWBAgent._on_stt_completed(text)
         │
         ▼
process_user_input(text)
         │
         ▼
[Continues as text input flow]
```

### Text Input Flow

```
User enters text + Ctrl+Enter
         │
         ▼
send_text()
         │
         ├─────────────────────────────┐
         ▼                             ▼
Create ChatMessage widget      ChatHistory.add_message()
Add to UI                              │
         │                             ▼
         ▼                      ChatHistory.save()
RWBAgent.process_user_input(text)
         │
         ▼
InputProcessorWorker created
         │
         ▼
astream() generator in ThreadPool
         │
         ▼
For each chunk:
├── text_update signal → UI update
├── split_into_sentences()
│           │
│           ▼
└── sentence_ready signal
            │
            ▼
    AudioProcessor.tts(sentence)
            │
            ▼
    TTS Queue → Kokoro → PyAudio playback
```

### Tool Usage Flow

```
Agent determines tool needed
         │
         ▼
ToolCallStarted event
         │
         ├──────────────────┐
         ▼                  ▼
feedback signal       TTS feedback
(UI update)           ("Researching now...")
         │
         ▼
Tool.execute()
         │
         ▼
External API call
(PubMed, DuckDuckGo, etc.)
         │
         ▼
ToolCallCompleted event
         │
         ├──────────────────┐
         ▼                  ▼
feedback signal       TTS feedback
                      ("Got results...")
         │
         ▼
Agent processes results
         │
         ▼
Generates response
         │
         ▼
[Normal streaming flow]
```

## Threading Model

```
Main Thread (Qt Event Loop)
├── UI rendering
├── User interaction
├── Signal/slot dispatching
└── Timer callbacks

QThreadPool (Global)
├── InputProcessorWorker (LLM streaming)
├── AudioProcessorWorker (STT)
└── Max concurrent: 4 (configurable)

TTS Queue Thread (Daemon)
├── Sequential TTS processing
├── Audio resampling
└── PyAudio playback
```

### Thread Synchronization

- **Queue.Queue** - Thread-safe TTS queue
- **Qt Signals** - Inter-thread communication
- **QMutex** - Resource locking where needed
- **Threading RLock** - TTS queue protection

## Signal Reference

### AudioProcessor Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `speaking` | None | TTS playback started |
| `done_speaking` | None | TTS playback finished |
| `stt_completed` | `str` | STT transcription complete |
| `error` | `str` | Processing error |

### RWBAgent Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `feedback` | `str, str` | Status message (message, type) |
| `text_update` | `str, str` | Text update (id, text) |
| `processing_complete` | None | Generation finished |

## Configuration Reference

### QSettings Keys

| Key | Type | Description |
|-----|------|-------------|
| `user` | JSON | User profile data |
| `assistant` | JSON | Assistant settings |
| `model/name` | str | Selected LLM model |
| `tts/voice` | str | Selected TTS voice |
| `window/size` | QSize | Window dimensions |
| `window/pos` | QPoint | Window position |
| `ui/history_splitter` | bytes | Splitter state |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_MODEL` | Ollama model name | `qwen2.5:14b-instruct-q8_0` |
| `AUTHOR_EMAIL` | NCBI Entrez email | `default@example.com` |

## Extension Points

### Adding New Tools

1. Create a Toolkit subclass
2. Register methods with docstrings
3. Add to agent tools list in `rwbagent.py`

### Adding New UI Components

1. Create widget in `rwb/audio/ui/`
2. Add styles to `styles.py`
3. Integrate in `assistant.py`

### Adding New Settings

1. Add property to `ContextManager`
2. Add UI in `SettingsDialog`
3. Add QSettings get/set calls

## Performance Considerations

### Audio Processing
- Recording: 44100 Hz, 1 channel, float32
- Resampling: Uses librosa (CPU-bound)
- Buffer size: 2048 frames
- Chunk size: 1024 bytes

### TTS Optimization
- Sequential processing (one sentence at a time)
- Queue-based (non-blocking from main thread)
- Mute support (skips TTS computation)

### UI Responsiveness
- All heavy processing in background threads
- Streaming text updates (incremental)
- Async signal communication
