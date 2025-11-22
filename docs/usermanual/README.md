# RWB User Manual

Welcome to the Researcher's Workbench User Manual. This documentation will help you get the most out of your AI research assistant.

## Documentation Overview

| Guide | Description |
|-------|-------------|
| [Getting Started](GETTING_STARTED.md) | Installation and first steps |
| [Features](FEATURES.md) | Complete feature reference |
| [Settings](SETTINGS.md) | Customization and configuration |
| [Troubleshooting](TROUBLESHOOTING.md) | Solutions to common problems |

---

## Quick Start

### 1. Install Prerequisites

```bash
# Install PortAudio (macOS)
brew install portaudio

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Set Up RWB

```bash
cd rwb_qt
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Download AI Model

```bash
ollama serve  # In one terminal
ollama pull qwen2.5:14b-instruct-q8_0  # In another terminal
```

### 4. Launch

```bash
python -m rwb
```

---

## What Can RWB Do?

### Voice Interaction
Talk to your computer naturally. Ask questions by voice, get answers spoken back to you.

### Research Tools
- **PubMed** - Search medical literature
- **Web Search** - Find current information
- **Wikipedia** - Quick knowledge lookup
- **Website Reading** - Extract content from URLs

### Smart Conversations
- Remembers conversation context
- Asks for clarification when needed
- Provides citations and references

### Privacy-Focused
- All AI processing happens locally
- No data sent to cloud services
- Your research stays on your computer

---

## Interface at a Glance

```
┌──────────────────────────────────────────────────────┐
│ ⚙️ Settings   ☐ Mute                                 │
├──────────────────────────────────────────────────────┤
│ [Chat] [History]                                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  💬 Your messages appear here                        │
│                                                      │
│  🤖 Assistant responses appear here                  │
│                                                      │
├──────────────────────────────────────────────────────┤
│ [📎] [Type message...         ] [🎤 Talk] [⏹ Stop] │
└──────────────────────────────────────────────────────┘
```

### Key Controls

| Control | Action |
|---------|--------|
| **Talk Button** | Hold to record voice |
| **Text Field** | Type messages (Ctrl+Enter to send) |
| **Stop Button** | Cancel current operation |
| **Mute Checkbox** | Disable voice output |
| **📎 Button** | Attach files |
| **⚙️ Button** | Open settings |

---

## Common Tasks

### Ask a Question
1. Hold the **Talk** button
2. Speak your question
3. Release the button
4. Wait for the response

### Search PubMed
> "Search PubMed for recent studies on immunotherapy"

### Get Definitions
> "What is CRISPR and how does it work?"

### Summarize Information
> "Summarize the key findings about mRNA vaccines"

---

## Tips for Best Results

### Voice Input
- Speak clearly at normal pace
- Minimize background noise
- Wait for silence before releasing button

### Better Answers
- Be specific in your questions
- Provide context when helpful
- Use proper terminology

### Managing Sessions
- Mute when you prefer reading
- Use Stop to cancel long responses
- Check History for past conversations

---

## System Requirements

### Minimum
- 8GB RAM
- Modern multi-core CPU
- Microphone and speakers

### Recommended
- 24GB RAM (Mac) or 16GB VRAM (GPU)
- SSD storage
- Quality headset

---

## Need Help?

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Ensure Ollama is running: `ollama serve`
3. Verify microphone permissions
4. Restart the application

---

## Document Navigation

| I want to... | See... |
|--------------|--------|
| Install RWB | [Getting Started](GETTING_STARTED.md#installation) |
| Learn the interface | [Getting Started](GETTING_STARTED.md#understanding-the-interface) |
| Use voice features | [Features - Voice](FEATURES.md#voice-interaction) |
| Search PubMed | [Features - PubMed](FEATURES.md#pubmed-search) |
| Change AI model | [Settings - Model](SETTINGS.md#model-settings) |
| Customize assistant | [Settings - Assistant](SETTINGS.md#assistant-settings) |
| Fix audio issues | [Troubleshooting - Audio](TROUBLESHOOTING.md#audio-issues) |
| Fix Ollama issues | [Troubleshooting - Ollama](TROUBLESHOOTING.md#ollama-issues) |

---

**Version:** 0.1.0
**Last Updated:** November 2025
