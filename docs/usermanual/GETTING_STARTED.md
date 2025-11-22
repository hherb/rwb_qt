# Getting Started with Researcher's Workbench

Welcome to the Researcher's Workbench (RWB)! This guide will help you install and start using the application.

## What is RWB?

RWB is a voice-enabled AI research assistant designed for biomedical researchers. It allows you to:

- **Talk to your computer** - Ask questions using your voice
- **Search medical literature** - Query PubMed using natural language
- **Get intelligent answers** - Powered by local AI that runs on your computer
- **Keep your data private** - Everything runs locally, no cloud services required

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | macOS 11+, Windows 10+, or Linux |
| **RAM** | 8 GB |
| **Storage** | 10 GB free space |
| **Processor** | Modern multi-core CPU |
| **Microphone** | Built-in or external microphone |
| **Speakers** | Built-in or external speakers/headphones |

### Recommended Requirements

For the best experience, we recommend:

| Component | Recommendation |
|-----------|----------------|
| **macOS** | Apple Silicon (M1/M2/M3) with 24GB RAM |
| **Windows/Linux** | NVIDIA GPU with 16GB+ VRAM |
| **Storage** | SSD for faster model loading |
| **Audio** | Quality headset with microphone |

## Installation

### Step 1: Install Required Software

#### Install Python

RWB requires Python 3.12 or later.

**macOS:**
```bash
# Using Homebrew
brew install python@3.12
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

#### Install Audio Libraries

**macOS:**
```bash
brew install portaudio
```

**Windows:**
- PortAudio is included with the Python package

**Linux (Ubuntu/Debian):**
```bash
sudo apt install portaudio19-dev
```

#### Install Ollama (AI Engine)

Ollama provides the AI brain for RWB.

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download from [ollama.com](https://ollama.com/download)
- Run the installer

### Step 2: Download RWB

```bash
# Clone or download the repository
git clone <repository-url>
cd rwb_qt
```

Or download and extract the ZIP file from the releases page.

### Step 3: Set Up RWB

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install RWB
pip install -e .
```

### Step 4: Download an AI Model

Start the Ollama server and download a model:

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Download the recommended model
ollama pull qwen2.5:14b-instruct-q8_0
```

**For computers with less memory**, use a smaller model:
```bash
ollama pull qwen2.5:7b-instruct-q4_0
```

### Step 5: Launch RWB

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Start RWB
python -m rwb
```

The application window should appear.

## First Launch

When RWB starts for the first time:

1. **Greeting**: The assistant will greet you by voice
2. **Ready State**: You'll see "Ready to record" in the status area
3. **Default Settings**: The app uses default user and assistant settings

### Initial Setup Recommended

Click the **Settings** button (gear icon) to personalize:

1. **User Tab**: Enter your name and background
2. **Assistant Tab**: Customize the assistant's name if desired
3. **Model Tab**: Verify the correct AI model is selected

## Quick Start Guide

### Talking to RWB

1. **Press and hold** the green "Talk" button
2. **Speak** your question clearly
3. **Release** the button when done
4. **Wait** for the response (you'll hear it spoken back)

### Typing to RWB

1. **Click** in the text input area
2. **Type** your question
3. **Press** Ctrl+Enter to send
4. **Read** the response in the chat area

### Example Questions to Try

**General Knowledge:**
- "What is machine learning?"
- "Explain the difference between DNA and RNA"

**PubMed Research:**
- "Search PubMed for recent studies on CRISPR gene therapy"
- "Find articles about COVID-19 vaccine efficacy"

**Web Search:**
- "What are the latest news about medical AI?"
- "Search for information about clinical trial phases"

## Understanding the Interface

```
┌─────────────────────────────────────────────────────────┐
│  ⚙️ Settings    ☐ Mute                                  │
├─────────────────────────────────────────────────────────┤
│  [Chat]  [History]                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Status: Ready to record                               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │           Chat messages appear here             │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────┐  [📎] [Talk] [Stop]  │
│  │ Type your message here...    │                      │
│  └──────────────────────────────┘                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Interface Elements

| Element | Purpose |
|---------|---------|
| **Settings (⚙️)** | Open settings dialog |
| **Mute Checkbox** | Silence voice output |
| **Chat Tab** | Active conversation |
| **History Tab** | Browse past conversations |
| **Status** | Shows current state |
| **Chat Area** | Displays messages |
| **Text Input** | Type messages here |
| **📎 Button** | Attach files |
| **Talk Button** | Hold to record voice |
| **Stop Button** | Cancel current operation |

## Tips for Best Results

### Voice Input Tips

1. **Speak clearly** at a normal pace
2. **Wait for silence** before releasing the button
3. **Use complete sentences** for better understanding
4. **Minimize background noise** when possible

### Getting Better Answers

1. **Be specific** - "Search PubMed for diabetes treatment in elderly patients" is better than "find diabetes stuff"
2. **Provide context** - "I'm researching cancer immunotherapy. What are the latest developments?"
3. **Ask follow-up questions** - The assistant remembers your conversation

### Managing Long Sessions

1. **Mute when needed** - Check the Mute box if you don't want voice output
2. **Use Stop button** - Cancel long responses if they're not what you need
3. **Check History** - Review past conversations in the History tab

## What's Next?

- Learn about all [Features](FEATURES.md)
- Customize your [Settings](SETTINGS.md)
- Get help with [Troubleshooting](TROUBLESHOOTING.md)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Ensure Ollama is running: `ollama serve`
3. Verify your microphone permissions
4. Restart the application

---

**Congratulations!** You're now ready to use the Researcher's Workbench. Happy researching!
