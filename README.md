# Researcher's Workbench (RWB)

A Qt-based voice assistant for biomedical research with real-time speech interaction and agentic AI capabilities.

## Overview

RWB is a desktop application that combines:

- **Real-time voice interaction** - Speech-to-text and text-to-speech, all running locally
- **Agentic AI capabilities** - LLM-powered research assistant with tool access
- **Research tools** - PubMed, DuckDuckGo, Wikipedia, and web scraping
- **Modern Qt interface** - Tabbed UI with chat and history views
- **Persistent storage** - Chat history and user preferences

## Features

### Voice Interface
- Real-time speech-to-text using Whisper (via fastrtc)
- High-quality text-to-speech using Kokoro (via fastrtc)
- Push-to-talk recording with visual feedback
- Mute control for TTS output

### Research Tools
- **PubMed Search** - Natural language queries to NCBI's medical literature database
- **Web Search** - DuckDuckGo integration for general queries
- **Wikipedia** - Quick access to encyclopedic knowledge
- **Website Scraping** - Extract content from web pages
- **Python Execution** - Run Python code for calculations and data processing

### Chat Interface
- Streaming responses with real-time display
- Markdown rendering with syntax highlighting
- Clickable links opening in external browser
- File attachment support (images, PDFs, documents)
- Persistent chat history with browsing capability

### Customization
- Configurable user profile for personalized interactions
- Assistant personality customization
- Model selection from available Ollama models
- Multiple TTS voice options

## Requirements

### Hardware
- **Minimum**: 8GB RAM, modern multi-core CPU
- **Recommended**:
  - macOS with Apple Silicon (M1+) and 24GB RAM, OR
  - Linux/Windows with NVIDIA GPU (16GB+ VRAM)
- SSD recommended for faster model loading

### Software
- Python 3.12 or later
- PortAudio library (for audio recording)
- Ollama server (for LLM inference)

## Installation

### 1. Install System Dependencies

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

### 2. Set Up Python Environment

```bash
# Clone the repository
git clone <repository-url>
cd rwb_qt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
# or
pip install -r requirements.txt
```

### 3. Install and Configure Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the server
ollama serve

# Pull a recommended model (in a new terminal)
ollama pull qwen2.5:14b-instruct-q8_0
```

For lower-end hardware, use a smaller model:
```bash
ollama pull qwen2.5:7b-instruct-q4_0
```

## Usage

### Starting the Application

```bash
python -m rwb
```

### Basic Interaction

1. **Voice Input**: Hold the "Talk" button while speaking, release to process
2. **Text Input**: Type in the text field and press Ctrl+Enter to send
3. **Stop Processing**: Click "Stop" to interrupt ongoing processing
4. **Mute TTS**: Check "Mute" to disable voice output

### Settings

Click the settings icon (gear) to configure:
- **User Profile**: Your name, title, and background for personalized responses
- **Assistant**: Customize the assistant's name and personality
- **Model**: Select from available Ollama models and TTS voices

### Chat History

Switch to the "History" tab to:
- Browse previous conversations
- View conversation details
- Delete old histories

## Project Structure

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
│   │   └── ui/           # UI components
│   ├── helpers/           # Utility functions
│   ├── llm/               # LLM utilities
│   ├── qt/                # Qt platform utilities
│   └── tools/             # Research tools
├── experimental/           # Experimental features
├── docs/                   # Documentation
│   └── developers/        # Developer documentation
├── pyproject.toml         # Project configuration
└── requirements.txt       # Dependencies
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_MODEL` | Default Ollama model | `qwen2.5:14b-instruct-q8_0` |
| `AUTHOR_EMAIL` | Email for NCBI Entrez API | `default@example.com` |

### Settings Storage

Settings are stored using Qt's QSettings:
- **macOS**: `~/Library/Preferences/com.rwb.app`
- **Linux**: `~/.config/RWB/`
- **Windows**: Windows Registry

Chat history is stored in: `~/.rwb/chat_history/`

## Dependencies

Core dependencies:
- **PySide6** (>=6.9.0) - Qt GUI framework
- **fastrtc** (>=0.0.20) - STT/TTS models
- **ollama** (>=0.4.7) - LLM client
- **agno** (>=1.2.15) - Agent framework
- **PyAudio** (>=0.2.14) - Audio I/O
- **Biopython** (>=1.85) - PubMed access

See `pyproject.toml` for complete dependency list.

## Development

### Developer Documentation

Comprehensive documentation is available in `docs/developers/`:

- **[Quickstart Guide](docs/developers/QUICKSTART.md)** - Get started with development
- **[Architecture Guide](docs/developers/ARCHITECTURE.md)** - System design and data flow
- **[API Reference](docs/developers/API_REFERENCE.md)** - Detailed module documentation

### Running from Source

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m rwb

# Or run directly
python main.py
```

### Building Packages

**PyInstaller (Cross-platform):**
```bash
pyinstaller rwb.spec
```

**py2app (macOS):**
```bash
python setup.py py2app
```

## Troubleshooting

### Common Issues

**Qt plugin errors (macOS):**
- The application automatically handles Qt plugin discovery
- If issues persist, try reinstalling PySide6: `pip install --force-reinstall PySide6`

**No audio input:**
- Check microphone permissions in system settings
- Verify PortAudio is installed correctly
- Check the correct audio device is selected

**Ollama connection failed:**
- Ensure Ollama server is running: `ollama serve`
- Verify the model is downloaded: `ollama list`
- Check server is accessible: `curl http://localhost:11434/api/tags`

**Slow response times:**
- Try a smaller model (e.g., 7B instead of 14B parameters)
- Ensure sufficient RAM is available
- Check GPU utilization if using CUDA

## License

MIT License

## Acknowledgments

- [Ollama](https://ollama.com/) for local LLM inference
- [fastrtc](https://github.com/FastRTC/fastrtc) for STT/TTS models
- [Agno](https://github.com/agno-dev/agno) for the agent framework
- [PySide6](https://doc.qt.io/qtforpython-6/) for the Qt bindings
