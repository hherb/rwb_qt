# RWB Developer Quickstart Guide

This guide will help you get started with contributing to the Researcher's Workbench (RWB) project - a Qt-based voice assistant for biomedical research.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - Required for the application
- **PortAudio** - Required for audio recording (PyAudio dependency)
- **Ollama** - Local LLM inference server
- **Git** - Version control

### Hardware Requirements

- **Minimum**: 8GB RAM, modern CPU
- **Recommended**:
  - macOS with M1+ chip and 24GB RAM, OR
  - Linux/Windows with NVIDIA GPU (16GB+ VRAM)
  - SSD for faster model loading

## Quick Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rwb_qt
```

### 2. Install System Dependencies

**macOS:**
```bash
brew install portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-dev
```

**Fedora:**
```bash
sudo dnf install portaudio-devel python3-devel
```

### 3. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 4. Install Python Dependencies

```bash
pip install -e .
# or using requirements.txt
pip install -r requirements.txt
```

### 5. Install and Start Ollama

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama server
ollama serve
```

### 6. Pull an LLM Model

```bash
# Recommended model
ollama pull qwen2.5:14b-instruct-q8_0

# Alternative smaller model for lower-end hardware
ollama pull qwen2.5:7b-instruct-q4_0
```

### 7. Run the Application

```bash
python -m rwb
```

## Project Structure Overview

```
rwb_qt/
├── main.py                 # Entry point
├── rwb/                    # Main package
│   ├── __main__.py        # Module entry point
│   ├── context.py         # Settings management
│   ├── agents/            # LLM agent implementation
│   │   ├── rwbagent.py   # Main agent class
│   │   └── worker.py     # Background workers
│   ├── audio/             # Audio processing & UI
│   │   ├── assistant.py  # Main GUI window
│   │   ├── processor.py  # STT/TTS processing
│   │   ├── recorder.py   # Audio recording
│   │   ├── chat_*.py     # Chat widgets
│   │   └── ui/           # UI components
│   ├── helpers/           # Utility functions
│   ├── llm/               # LLM utilities
│   ├── qt/                # Qt platform utilities
│   └── tools/             # Research tools (PubMed, etc.)
├── experimental/           # Experimental features
└── docs/                   # Documentation
```

## Key Concepts

### 1. Main Entry Point

The application starts from `rwb/__main__.py`:
- Sets up Qt plugin manager (important for macOS)
- Creates the Qt application
- Initializes and shows the `AudioAssistant` main window

### 2. Main Window (AudioAssistant)

Located in `rwb/audio/assistant.py`, this is the central UI class:
- Manages the tabbed interface (Chat + History)
- Handles user input (voice and text)
- Coordinates the agent and audio processor

### 3. Agent (RWBAgent)

Located in `rwb/agents/rwbagent.py`:
- Handles LLM inference using Agno framework with Ollama
- Manages tools (DuckDuckGo, PubMed, Wikipedia, etc.)
- Streams responses for real-time display

### 4. Audio Processing

Located in `rwb/audio/processor.py`:
- Manages speech-to-text (STT) using Whisper via fastrtc
- Manages text-to-speech (TTS) using Kokoro via fastrtc
- Thread-safe queue-based processing

### 5. Settings Management

Located in `rwb/context.py`:
- `ContextManager` singleton manages all persistent settings
- Uses Qt's QSettings for platform-native storage
- Stores user profile, assistant settings, model preferences

## Development Workflow

### Running Tests

```bash
# Test agent functionality
python -c "from rwb.agents.rwbagent import RWBAgent; a = RWBAgent(); print('Agent OK')"

# Test STT/TTS models
python -c "from fastrtc import get_stt_model, get_tts_model; print('Models OK')"
```

### Common Development Tasks

#### Changing Default Model

Edit `rwb/context.py` or set environment variable:
```bash
export DEFAULT_MODEL="your-model-name"
```

#### Adding a New Tool

1. Create a Toolkit subclass in `rwb/tools/`:
```python
from agno.tools import Toolkit

class MyTool(Toolkit):
    def __init__(self):
        super().__init__(name="my_tool")
        self.register(self.my_function)

    def my_function(self, query: str) -> str:
        """Description shown to the agent."""
        return "result"
```

2. Add to agent in `rwb/agents/rwbagent.py`:
```python
from rwb.tools.my_tool import MyTool

# In RWBAgent.__init__:
tools=[
    DuckDuckGoTools(),
    MyTool(),  # Add here
    ...
]
```

#### Modifying UI Components

- Button styles: `rwb/audio/ui/styles.py`
- UI widgets: `rwb/audio/ui/components.py`
- Settings dialog: `rwb/audio/ui/settings_dialog.py`

### Debugging Tips

1. **Check console output** - Most operations print debug info
2. **Agent feedback** - Watch for `[INFO]`, `[DEBUG]`, `[ERROR]` messages
3. **Qt plugins issue** (macOS): Ensure `QtPluginManager.setup_plugins()` succeeds
4. **Ollama not responding**: Verify server is running with `ollama list`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_MODEL` | Default Ollama model name | `qwen2.5:14b-instruct-q8_0` |
| `AUTHOR_EMAIL` | Email for NCBI Entrez API | `default@example.com` |

## Configuration Files

- `pyproject.toml` - Project metadata and dependencies
- `requirements.txt` - Simplified dependency list
- `rwb.spec` - PyInstaller packaging configuration
- `setup.py` - py2app packaging configuration

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md) for detailed system design
- Check the [API Reference](API_REFERENCE.md) for module documentation
- Explore `experimental/` for development examples

## Getting Help

- Check existing code comments and docstrings
- Review the architecture documentation
- Look at experimental scripts for usage examples
