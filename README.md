# Researcher's Worbench - now with QT based UI with real time Voice Assistant
** work in progress, functionality only partially implemented yet; a lot of functionality still needs to be ported from my old web UI based RWB project

A biomedical sciences focussed agentic research interface resembling a chatbot, but
- all inference including text-to-speech & speech-to-text generation happening locally
- agents have long term memory and are able of searching the web, services such as pubmed, and local databases
- agents can compose a reasobnable draft of a scientific publication with human-in-the-loop research and composition process
A voice assistant application that uses speech-to-text, text-to-speech, and natural language processing to enable voice-based interactions.

## Features

- Crafting and optimising database queries (eg pubmed) from natural language questions
- keeping track of references and data sources long term, with retrieval by natural language questioning (variety of RAG techniques)
- Real-time speech-to-text conversion
- Natural language processing using Ollama
- High-quality text-to-speech synthesis
- Modern Qt-based user interface
- Support for interrupting and stopping processing

## Requirements

- a reasonably powerful computer with sufficient and fast enough memory (a mac >= M1 processor with at least 24GB or a NVIDIA GPU with at least 16GB RAM will do)
- Python 3.12 or later
- PortAudio (for PyAudio)
- Ollama server running locally
- FastRTC library
- Agno library
- PostgresSQL server with pgvector extension

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
