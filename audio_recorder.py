import sys
import os
import pyaudio
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from fastrtc import get_stt_model, get_tts_model, KokoroTTSOptions
from ollama import chat
import librosa
import asyncio
from concurrent.futures import ThreadPoolExecutor
import site
import json
import tempfile
from pathlib import Path
import subprocess

class QtPluginManager:
    """Manages Qt platform plugins with verification, caching, and fallback mechanisms"""
    
    def __init__(self):
        self.cache_file = Path(tempfile.gettempdir()) / "qt_plugins_cache.json"
        self.cached_path = None
        self.verified_paths = set()
        
    def load_cache(self):
        """Load cached plugin path from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    if data.get('path') and os.path.exists(data['path']):
                        self.cached_path = data['path']
                        print(f"Loaded cached Qt plugin path: {self.cached_path}")
        except Exception as e:
            print(f"Error loading plugin cache: {e}")
    
    def save_cache(self, path):
        """Save successful plugin path to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({'path': path}, f)
            self.cached_path = path
        except Exception as e:
            print(f"Error saving plugin cache: {e}")
    
    def verify_plugins(self, path):
        """Verify that Qt plugins at the given path are working"""
        if path in self.verified_paths:
            return True
            
        try:
            # Simple verification: check if the cocoa plugin exists
            cocoa_plugin = os.path.join(path, "libqcocoa.dylib")
            if os.path.exists(cocoa_plugin):
                print(f"Found cocoa plugin at: {cocoa_plugin}")
                self.verified_paths.add(path)
                return True
            else:
                print(f"Cocoa plugin not found at: {cocoa_plugin}")
                return False
        except Exception as e:
            print(f"Plugin verification failed for {path}: {e}")
            return False
    
    def get_possible_plugin_paths(self):
        """Get all possible plugin paths in order of priority"""
        paths = []
        
        # 1. Check cached path first
        if self.cached_path and os.path.exists(self.cached_path):
            paths.append(self.cached_path)
            print(f"Added cached path: {self.cached_path}")
        
        # 2. Check virtual environment first (highest priority)
        if hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'):
            # We're in a virtual environment
            venv_path = sys.prefix
            possible_paths = [
                os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "plugins", "platforms"),
                os.path.join(venv_path, "lib", "site-packages", "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(venv_path, "lib", "site-packages", "PySide6", "plugins", "platforms"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    paths.append(path)
                    print(f"Added virtual environment path: {path}")
        
        # 3. Check PySide6 installation
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "PySide6"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Location:'):
                        location = line.split(':', 1)[1].strip()
                        possible_paths = [
                            os.path.join(location, "PySide6", "Qt", "plugins", "platforms"),
                            os.path.join(location, "PySide6", "plugins", "platforms"),
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                paths.append(path)
                                print(f"Added PySide6 installation path: {path}")
        except Exception as e:
            print(f"Error finding PySide6 location: {e}")
        
        # 4. Check system-wide site-packages
        for site_dir in site.getsitepackages():
            possible_paths = [
                os.path.join(site_dir, "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(site_dir, "PySide6", "plugins", "platforms"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    paths.append(path)
                    print(f"Added system site-packages path: {path}")
        
        # 5. Check user's home directory
        home_paths = [
            os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PySide6/Qt/plugins/platforms"),
            os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PySide6/plugins/platforms"),
        ]
        for path in home_paths:
            if os.path.exists(path):
                paths.append(path)
                print(f"Added home directory path: {path}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        return unique_paths
    
    def setup_plugins(self):
        """Setup Qt plugins with verification and fallback"""
        if sys.platform != "darwin":  # Only needed for macOS
            return True
        
        # Load cached path
        self.load_cache()
        
        # Try all possible paths
        paths = self.get_possible_plugin_paths()
        if not paths:
            print("No Qt plugin paths found!")
            return False
            
        print("\nTrying Qt plugin paths in order of priority:")
        for path in paths:
            print(f"\nAttempting path: {path}")
            
            # Set the plugin path
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = path
            
            # Set additional environment variables needed for Qt
            if hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'):
                # We're in a virtual environment
                venv_path = sys.prefix
                qt_lib_path = os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "Qt", "lib")
                if os.path.exists(qt_lib_path):
                    os.environ["DYLD_LIBRARY_PATH"] = qt_lib_path
                    os.environ["LD_LIBRARY_PATH"] = qt_lib_path
                    print(f"Set Qt library path: {qt_lib_path}")
            
            if self.verify_plugins(path):
                print(f"Successfully verified Qt plugins at: {path}")
                self.save_cache(path)
                return True
        
        # If we get here, no path worked
        print("\nWarning: Could not find working Qt platform plugins.")
        print("Try running: uv pip install --reinstall pyside6")
        return False

# Create and setup plugin manager
plugin_manager = QtPluginManager()
if not plugin_manager.setup_plugins():
    print("Failed to setup Qt plugins. The application might not work correctly.")
    sys.exit(1)

class AudioProcessor(QThread):
    """Thread for processing audio asynchronously"""
    finished = Signal(str, str)  # Signal for when processing is complete (user_text, assistant_text)
    error = Signal(str)  # Signal for errors
    speaking = Signal()  # Signal for when speaking starts
    done_speaking = Signal()  # Signal for when speaking ends
    
    def __init__(self, audio_data, sample_rate, stt_model, tts_model, tts_options):
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.tts_options = tts_options
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.audio = pyaudio.PyAudio()
        
    def run(self):
        try:
            # Convert audio to text
            user_text = self.stt_model.stt((self.sample_rate, self.audio_data))
            
            # Get LLM response
            response = chat(model='granite3.2:8b-instruct-q8_0', messages=[
                {
                    'role': 'user',
                    'content': user_text,
                },
            ])
            
            assistant_text = response['message']['content']
            
            # Emit the results
            self.finished.emit(user_text, assistant_text)
            
            # Start speaking
            self.speaking.emit()
            
            # Text to speech and play audio
            output_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            
            try:
                # Get the TTS stream
                tts_stream = self.tts_model.stream_tts_sync(assistant_text, options=self.tts_options)
                
                # Process each chunk
                for chunk in tts_stream:
                    if isinstance(chunk, tuple):
                        if len(chunk) > 0:
                            sample_rate, audio_data = chunk
                            if isinstance(audio_data, np.ndarray):
                                # Resample from Kokoro's rate to PyAudio's rate
                                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
                                audio_bytes = audio_data.tobytes()
                                output_stream.write(audio_bytes)
                    else:
                        if isinstance(chunk, np.ndarray):
                            audio_data = librosa.resample(chunk, orig_sr=24000, target_sr=44100)
                            audio_bytes = audio_data.tobytes()
                            output_stream.write(audio_bytes)
                        elif isinstance(chunk, bytes):
                            audio_array = np.frombuffer(chunk, dtype=np.float32)
                            audio_array = librosa.resample(audio_array, orig_sr=24000, target_sr=44100)
                            audio_bytes = audio_array.tobytes()
                            output_stream.write(audio_bytes)
                
            finally:
                output_stream.stop_stream()
                output_stream.close()
                self.done_speaking.emit()
                
        except Exception as e:
            self.error.emit(str(e))
            import traceback
            traceback.print_exc()
        finally:
            self.audio.terminate()

class AudioAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 600, 500)
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100  # PyAudio output rate
        self.KOKORO_RATE = 24000  # Kokoro's native rate
        self.recording = False
        self.frames = []
        self.processor = None  # Reference to the current audio processor
        
        # Initialize models
        self.stt_model = get_stt_model()
        self.tts_model = get_tts_model(model="kokoro")
        self.tts_options = KokoroTTSOptions(
            voice="bf_emma",
            speed=1.0,
            lang="en-us"
        )
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Create UI
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Ready to talk")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Conversation display
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        layout.addWidget(self.conversation_display)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Talk button
        self.talk_button = QPushButton("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 20px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
        self.talk_button.pressed.connect(self.start_recording)
        self.talk_button.released.connect(self.stop_recording)
        button_layout.addWidget(self.talk_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 20px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.stop_button)
        
        layout.addWidget(button_container, alignment=Qt.AlignCenter)
    
    def stop_processing(self):
        """Stop any ongoing audio processing"""
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
            self.processor = None
            self.status_label.setText("Processing stopped")
            self.talk_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.talk_button.setText("Hold to Talk")
            self.talk_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 20px;
                    font-size: 16px;
                    border-radius: 10px;
                }
                QPushButton:pressed {
                    background-color: #45a049;
                }
            """)
    
    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            
            # Open input stream
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.talk_button.setText("Recording...")
            self.talk_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 20px;
                    font-size: 16px;
                    border-radius: 10px;
                }
            """)
            self.status_label.setText("Listening...")
            
            # Start recording timer
            self.record_timer = QTimer()
            self.record_timer.timeout.connect(self.record_audio)
            self.record_timer.start(10)
    
    def record_audio(self):
        if self.recording:
            try:
                data = self.input_stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                print(f"Error recording audio: {e}")
    
    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.record_timer.stop()
            
            self.input_stream.stop_stream()
            self.input_stream.close()
            
            self.talk_button.setText("Processing...")
            self.status_label.setText("Processing your request...")
            self.talk_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Convert audio to numpy array
            audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
            audio_data = audio_data.reshape(1, -1)
            
            # Start the audio processor thread
            self.processor = AudioProcessor(
                audio_data=audio_data,
                sample_rate=self.RATE,
                stt_model=self.stt_model,
                tts_model=self.tts_model,
                tts_options=self.tts_options
            )
            
            # Connect signals
            self.processor.finished.connect(self.handle_processing_finished)
            self.processor.error.connect(self.handle_processing_error)
            self.processor.speaking.connect(self.handle_speaking_started)
            self.processor.done_speaking.connect(self.handle_speaking_ended)
            
            # Start the processor
            self.processor.start()
    
    @Slot(str, str)
    def handle_processing_finished(self, user_text, assistant_text):
        # Update UI with conversation
        self.conversation_display.append(f"You: {user_text}")
        self.conversation_display.append(f"Assistant: {assistant_text}")
        self.conversation_display.append("")
    
    @Slot(str)
    def handle_processing_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.talk_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.talk_button.setText("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 20px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
    
    @Slot()
    def handle_speaking_started(self):
        self.status_label.setText("Speaking...")
    
    @Slot()
    def handle_speaking_ended(self):
        self.status_label.setText("Ready to talk")
        self.talk_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.talk_button.setText("Hold to Talk")
        self.talk_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 20px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
    
    def closeEvent(self, event):
        if self.recording:
            self.stop_recording()
        if self.processor and self.processor.isRunning():
            self.processor.terminate()
            self.processor.wait()
        self.audio.terminate()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioAssistant()
    window.show()
    sys.exit(app.exec()) 