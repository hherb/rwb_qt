# Voice Assistant

A voice assistant application that uses speech-to-text, text-to-speech, and natural language processing to enable voice-based interactions.

## Features

- Real-time speech-to-text conversion
- Natural language processing using Ollama
- High-quality text-to-speech synthesis
- Modern Qt-based user interface
- Support for interrupting and stopping processing

## Requirements

- Python 3.12 or later
- PortAudio (for PyAudio)
- Ollama server running locally

## Installation

1. Install PortAudio:
   ```bash
   # macOS
   brew install portaudio

   # Ubuntu/Debian
   sudo apt-get install portaudio19-dev
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Ollama server:
   ```bash
   ollama serve
   ```

5. Pull the required model:
   ```bash
   ollama pull granite3.2:8b-instruct-q8_0
   ```

## Usage

1. Start the application:
   ```bash
   python -m rwb
   ```

2. Hold the "Talk" button while speaking
3. Release the button to process your speech
4. Listen to the assistant's response
5. Use the "Stop" button to interrupt processing if needed

## Development

The project is organized into several modules:

- `rwb/audio/assistant.py`: Main GUI application
- `rwb/audio/processor.py`: Audio processing and model interaction
- `rwb/qt/plugin_manager.py`: Qt plugin management for macOS compatibility

## License

MIT License
