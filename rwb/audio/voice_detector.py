"""Voice Activity Detection module.

This module provides voice activity detection capabilities using Silero VAD,
enabling automated recording when voice is detected.
"""

import numpy as np
import threading
import time
import torch
import pyaudio
import queue
from typing import Optional, Callable, List, Union, Tuple
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class VoiceDetectorSignals(QObject):
    """Signals for the voice detector events."""
    
    voice_detected = Signal()  # Signal emitted when voice is detected
    voice_stopped = Signal()   # Signal emitted when voice stops
    recording_complete = Signal(np.ndarray)  # Signal emitted with recorded audio when complete


class VoiceDetector(QObject):
    """Voice activity detector using Silero VAD.
    
    This class provides continuous monitoring for voice activity using Silero VAD
    and starts/stops recording automatically when voice is detected.
    """
    
    def __init__(self, 
                 sample_rate: int = 16000, 
                 chunk_size: int = 512,
                 vad_threshold: float = 0.5, 
                 silence_duration: float = 1.5):
        """Initialize the voice detector.
        
        Args:
            sample_rate: The sample rate to use for recording (default: 16000 Hz)
            chunk_size: Size of audio chunks for processing
            vad_threshold: Threshold for voice detection (0.0-1.0)
            silence_duration: Duration of silence before stopping recording (seconds)
        """
        super().__init__()
        
        # Audio parameters
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # VAD parameters
        self.vad_threshold = vad_threshold
        self.silence_duration = silence_duration
        
        # Audio state and buffers
        self.listening = False
        self.recording = False
        self.frames: List[bytes] = []
        self.last_voice_time = 0
        self.audio_buffer = queue.Queue()
        
        # Audio stream objects
        self.audio = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        
        # QTimer for processing audio
        self.process_timer: Optional[QTimer] = None
        
        # Create signals object
        self.signals = VoiceDetectorSignals()
        
        # Load Silero VAD model
        self._init_vad_model()
    
    def _init_vad_model(self) -> None:
        """Initialize the Silero VAD model."""
        try:
            # Model initialization from torch hub
            self.vad_model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            
            # Get functions from utils
            self.get_speech_timestamps = self.utils[0]
            self.get_speech_ts_adaptive = self.utils[2]
            self.save_audio = self.utils[3]
            
            # Ensure the model is in evaluation mode and move to GPU if available
            self.vad_model.eval()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.vad_model = self.vad_model.to(self.device)
            
            print(f"Silero VAD model initialized on {self.device}")
        except Exception as e:
            print(f"Error initializing Silero VAD model: {e}")
            self.vad_model = None
            raise
    
    def start_listening(self) -> None:
        """Start listening for voice activity."""
        if self.listening:
            return
        
        try:
            # Open audio input stream
            self.input_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start the stream
            self.input_stream.start_stream()
            
            # Reset state
            self.listening = True
            self.recording = False
            self.frames = []
            self.last_voice_time = 0
            
            # Start processing timer
            self.process_timer = QTimer()
            self.process_timer.timeout.connect(self._process_buffer)
            self.process_timer.start(100)  # Process every 100ms
            
            print("Voice detector started listening")
            
        except Exception as e:
            print(f"Error starting voice detector: {e}")
            if self.input_stream:
                self.input_stream.close()
            self.input_stream = None
    
    def stop_listening(self) -> None:
        """Stop listening for voice activity."""
        if not self.listening:
            return
        
        try:
            # Stop processing timer
            if self.process_timer:
                self.process_timer.stop()
                self.process_timer = None
            
            # Stop and close audio stream
            if self.input_stream:
                if self.input_stream.is_active():
                    self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            # Reset state
            self.listening = False
            self.recording = False
            
            print("Voice detector stopped listening")
            
        except Exception as e:
            print(f"Error stopping voice detector: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process incoming audio data.
        
        This is called by the audio input stream for each chunk of audio data.
        """
        if self.listening:
            # Add audio data to buffer for processing
            self.audio_buffer.put(in_data)
            
            # If we're currently recording, add the frame to our recording
            if self.recording:
                self.frames.append(in_data)
        
        # Continue receiving audio
        return (None, pyaudio.paContinue)
    
    def _process_buffer(self) -> None:
        """Process audio buffer for voice activity detection."""
        if not self.listening or self.vad_model is None:
            return
        
        # Process all available data in the buffer
        chunks = []
        while not self.audio_buffer.empty():
            try:
                chunk = self.audio_buffer.get_nowait()
                chunks.append(chunk)
            except queue.Empty:
                break
        
        if not chunks:
            # Check if we've been recording but voice has stopped
            if self.recording and time.time() - self.last_voice_time > self.silence_duration:
                self._stop_recording()
            return
        
        # Convert audio chunks to numpy array
        audio_data = np.frombuffer(b''.join(chunks), dtype=np.float32)
        
        # Process with VAD
        self._detect_voice(audio_data)
    
    def _detect_voice(self, audio_data: np.ndarray) -> None:
        """Process audio data with Silero VAD to detect voice activity.
        
        Args:
            audio_data: Audio data as numpy array
        """
        # Convert to tensor and process with VAD
        try:
            tensor_data = torch.from_numpy(audio_data).to(self.device)
            
            # Get voice probability
            with torch.no_grad():
                speech_prob = self.vad_model(tensor_data, self.sample_rate).item()
            
            # Voice detection based on threshold
            is_voice = speech_prob > self.vad_threshold
            
            if is_voice:
                # Update the last voice time
                self.last_voice_time = time.time()
                
                # If we're not recording, start recording
                if not self.recording:
                    self._start_recording()
            
            # If we're recording but haven't heard voice for a while, stop recording
            elif self.recording and time.time() - self.last_voice_time > self.silence_duration:
                self._stop_recording()
                
        except Exception as e:
            print(f"Error in voice detection: {e}")
    
    def _start_recording(self) -> None:
        """Start recording audio when voice is detected."""
        if not self.recording:
            self.recording = True
            self.frames = []  # Clear any previous frames
            self.signals.voice_detected.emit()
            print("Voice detected - recording started")
    
    def _stop_recording(self) -> None:
        """Stop recording and process the recorded audio."""
        if self.recording:
            self.recording = False
            self.signals.voice_stopped.emit()
            print("Voice stopped - recording stopped")
            
            # Convert frames to numpy array
            if self.frames:
                audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
                
                # Emit signal with recorded audio
                self.signals.recording_complete.emit(audio_data)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_listening()
        self.audio.terminate()
        print("Voice detector resources cleaned up")


if __name__ == "__main__":
    # Simple test code to demonstrate usage
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            
            self.setWindowTitle("Voice Detector Test")
            self.setGeometry(100, 100, 400, 200)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            self.status_label = QLabel("Status: Not Listening")
            layout.addWidget(self.status_label)
            
            self.start_button = QPushButton("Start Listening")
            self.start_button.clicked.connect(self.start_listening)
            layout.addWidget(self.start_button)
            
            self.stop_button = QPushButton("Stop Listening")
            self.stop_button.clicked.connect(self.stop_listening)
            self.stop_button.setEnabled(False)
            layout.addWidget(self.stop_button)
            
            # Initialize voice detector
            self.voice_detector = VoiceDetector()
            
            # Connect signals
            self.voice_detector.signals.voice_detected.connect(self.on_voice_detected)
            self.voice_detector.signals.voice_stopped.connect(self.on_voice_stopped)
            self.voice_detector.signals.recording_complete.connect(self.on_recording_complete)
        
        def start_listening(self):
            self.voice_detector.start_listening()
            self.status_label.setText("Status: Listening for voice")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        
        def stop_listening(self):
            self.voice_detector.stop_listening()
            self.status_label.setText("Status: Not Listening")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        
        def on_voice_detected(self):
            self.status_label.setText("Status: Voice Detected - Recording...")
        
        def on_voice_stopped(self):
            self.status_label.setText("Status: Voice Stopped - Processing...")
        
        def on_recording_complete(self, audio_data):
            duration = len(audio_data) / self.voice_detector.sample_rate
            self.status_label.setText(f"Status: Recording Complete - {duration:.2f}s")
            print(f"Recorded {len(audio_data)} samples ({duration:.2f}s)")
        
        def closeEvent(self, event):
            self.voice_detector.cleanup()
            event.accept()
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
