# RWB Developer Documentation

Welcome to the developer documentation for the Researcher's Workbench (RWB) project.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Quickstart Guide](QUICKSTART.md) | Get started with development quickly |
| [Architecture Guide](ARCHITECTURE.md) | System design and component interactions |
| [API Reference](API_REFERENCE.md) | Detailed module and class documentation |

## Quick Links

### Getting Started

1. **[Prerequisites](QUICKSTART.md#prerequisites)** - What you need before starting
2. **[Quick Setup](QUICKSTART.md#quick-setup)** - Step-by-step installation
3. **[Project Structure](QUICKSTART.md#project-structure-overview)** - Directory layout

### Understanding the System

1. **[System Overview](ARCHITECTURE.md#system-overview)** - High-level architecture
2. **[Component Details](ARCHITECTURE.md#component-details)** - In-depth component docs
3. **[Data Flow](ARCHITECTURE.md#data-flow-diagrams)** - How data moves through the system
4. **[Threading Model](ARCHITECTURE.md#threading-model)** - Concurrency design

### API Documentation

1. **[Core Modules](API_REFERENCE.md#core-modules)** - Context and entry point
2. **[Agent Modules](API_REFERENCE.md#agent-modules)** - LLM agent and workers
3. **[Audio Modules](API_REFERENCE.md#audio-modules)** - STT, TTS, recording
4. **[UI Modules](API_REFERENCE.md#ui-modules)** - Interface components
5. **[Tool Modules](API_REFERENCE.md#tool-modules)** - Research tools

## Key Concepts

### Application Flow

```
User Input → AudioAssistant → RWBAgent → Ollama LLM
                    ↓              ↓
              AudioProcessor    Tools
                    ↓              ↓
                STT/TTS       PubMed, Web, etc.
```

### Main Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `AudioAssistant` | Main GUI window | `rwb/audio/assistant.py` |
| `RWBAgent` | LLM inference & tools | `rwb/agents/rwbagent.py` |
| `AudioProcessor` | STT/TTS handling | `rwb/audio/processor.py` |
| `ContextManager` | Settings management | `rwb/context.py` |

### Technologies Used

| Technology | Purpose |
|------------|---------|
| **PySide6** | Qt-based GUI framework |
| **Ollama** | Local LLM inference |
| **fastrtc** | STT (Whisper) and TTS (Kokoro) |
| **Agno** | Agent framework with tools |
| **PyAudio** | Audio recording/playback |
| **Biopython** | PubMed API access |

## Common Development Tasks

### Adding a New Feature

1. Identify the relevant module(s)
2. Read existing code patterns
3. Add your implementation
4. Connect signals if needed
5. Test thoroughly

### Adding a New Tool

```python
# 1. Create tool in rwb/tools/my_tool.py
from agno.tools import Toolkit

class MyTool(Toolkit):
    def __init__(self):
        super().__init__(name="my_tool")
        self.register(self.search)

    def search(self, query: str) -> str:
        """Search for something."""
        return "results"

# 2. Add to rwb/agents/rwbagent.py
from rwb.tools.my_tool import MyTool

# In agent initialization:
tools=[
    ...,
    MyTool(),
]
```

### Modifying the UI

1. **Styles**: Edit `rwb/audio/ui/styles.py`
2. **Components**: Edit `rwb/audio/ui/components.py`
3. **Main Window**: Edit `rwb/audio/assistant.py`
4. **Dialogs**: Edit `rwb/audio/ui/settings_dialog.py`

### Debugging

```python
# Enable verbose agent output
agent.feedback.connect(lambda msg, t: print(f"[{t}] {msg}"))

# Check model status
import ollama
print(ollama.list())

# Test STT/TTS
from fastrtc import get_stt_model, get_tts_model
stt = get_stt_model()
tts = get_tts_model(model="kokoro")
```

## Contributing Guidelines

1. **Code Style**: Follow existing patterns in the codebase
2. **Documentation**: Add docstrings to all public methods
3. **Testing**: Test your changes with voice and text input
4. **Commits**: Write clear, descriptive commit messages
5. **Pull Requests**: Include description of changes and testing done

## Support

- Review existing code for patterns and examples
- Check the experimental/ directory for development examples
- Refer to external documentation:
  - [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
  - [Ollama Documentation](https://ollama.com/docs)
  - [Agno Documentation](https://docs.agno.dev/)
