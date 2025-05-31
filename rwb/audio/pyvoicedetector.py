import sys
import os
import numpy as np
import torch
import queue
import threading
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QPushButton, QLabel, QWidget, QProgressBar)
from PySide6.QtCore import QTimer, Signal, Slot, QObject
import pyaudio
from typing import Callable, Optional

# For Silero VAD
import torch
import torchaudio


class VoiceActivityDetector:
    """Wrapper for Silero VAD model"""
    
    def __init__(self, threshold=0.5, sampling_rate=16000):
        """
        Initialize the Silero VAD model
        
        Args:
            threshold: VAD threshold (0.0-1.0), higher values = less sensitive
            sampling_rate: audio sampling rate (Hz)
        """
        self.threshold = threshold
        self.sampling_rate = sampling_rate
        
        # Load Silero VAD model
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', 
                                     model='silero_vad', 
                                     force_reload=False)
        
        self.model = model
        self.get_speech_timestamps = utils[0]
        self.get_speech_ts_adaptive = utils[4]
        
    def is_speech(self, audio_chunk):
        """
        Check if audio chunk contains speech
        
        Args:
            audio_chunk: numpy array of audio samples (should be mono)
            
        Returns:
            bool: True if speech detected, False otherwise
        """
        # Convert numpy array to torch tensor
        tensor = torch.from_numpy(audio_chunk).float()
        
        # Normalize if needed
        if tensor.abs().max() > 1.0:
            tensor = tensor / tensor.abs().max()
            
        # Get speech timestamps
        speech_dict = self.get_speech_timestamps(tensor, 
                                                self.model,
                                                threshold=self.threshold,
                                                sampling_rate=self.sampling_rate)
        
        # If we have any speech segments
        return len(speech_dict) > 0


class AudioProcessor(QObject):
    """Audio processing thread that runs VAD on captured audio"""
    
    # Signal emitted when voice is detected
    voice_detected = Signal()
    
    # Signal for audio level for visualizing
    audio_level = Signal(float)
    
    def __init__(self, vad, callback: Optional[Callable] = None):
        super().__init__()
        self.vad = vad
        self.callback = callback
        
        # Audio parameters
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 16000  # Silero works best with 16kHz
        self.chunk = 1024  # 64ms at 16kHz
        
        # Processing state
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        
    def start(self):
        """Start audio capture and processing"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Open audio stream
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            stream_callback=self._audio_callback
        )
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def stop(self):
        """Stop audio capture and processing"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback to capture audio"""
        if self.is_running:
            # Convert raw data to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Calculate audio level for visualization (RMS)
            level = np.sqrt(np.mean(np.square(audio_data)))
            self.audio_level.emit(level)
            
            # Add to processing queue
            self.audio_queue.put(audio_data.copy())
            
        return (in_data, pyaudio.paContinue)
        
    def _process_audio(self):
        """Process audio data with VAD in a separate thread"""
        window_size = 5  # Number of chunks to analyze together (~320ms)
        audio_window = []
        
        while self.is_running:
            try:
                # Get audio chunk from queue
                audio_data = self.audio_queue.get(timeout=0.5)
                
                # Add to window
                audio_window.append(audio_data)
                
                # Keep window at fixed size
                if len(audio_window) > window_size:
                    audio_window.pop(0)
                
                # When we have enough data, run VAD
                if len(audio_window) == window_size:
                    # Concatenate chunks
                    window_data = np.concatenate(audio_window)
                    
                    # Check if voice is detected
                    if self.vad.is_speech(window_data):
                        # Emit signal
                        self.voice_detected.emit()
                        
                        # Call callback if provided
                        if self.callback:
                            self.callback()
                        
                        # Give some time before next detection
                        time.sleep(0.5)
                        
                        # Clear window to prevent repeated detections
                        audio_window = []
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio processing: {e}")
                break


class VoiceDetectionWidget(QWidget):
    """Main widget for voice activity detection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Audio level indicator 
        self.level_bar = QProgressBar()
        self.level_bar.setMinimum(0)
        self.level_bar.setMaximum(100)
        layout.addWidget(self.level_bar)
        
        # Button to start/stop
        self.toggle_button = QPushButton("Start Listening")
        self.toggle_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.toggle_button)
        
        # Set layout
        self.setLayout(layout)
        
        # Initialize VAD
        self.vad = VoiceActivityDetector(threshold=0.5, sampling_rate=16000)
        
        # Initialize audio processor
        self.audio_processor = AudioProcessor(self.vad, callback=self.on_voice_detected)
        self.audio_processor.voice_detected.connect(self.on_voice_signal)
        self.audio_processor.audio_level.connect(self.update_level)
        
        # Recording state
        self.is_recording = False
        
        # Timer to reset status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.reset_status)
        self.status_timer.setSingleShot(True)
        
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            # Start recording
            self.audio_processor.start()
            self.toggle_button.setText("Stop Listening")
            self.status_label.setText("Listening for voice...")
            self.is_recording = True
        else:
            # Stop recording
            self.audio_processor.stop()
            self.toggle_button.setText("Start Listening")
            self.status_label.setText("Ready")
            self.is_recording = False
            
    def update_level(self, level):
        """Update audio level indicator"""
        # Scale to 0-100 for progress bar
        scaled_level = min(int(level * 500), 100)
        self.level_bar.setValue(scaled_level)
        
    @Slot()
    def on_voice_signal(self):
        """Handle voice detected signal"""
        if self.is_recording:
            self.status_label.setText("Voice detected!")
            self.status_timer.start(1000)  # Reset after 1 second
            
    def on_voice_detected(self):
        """Callback function when voice is detected"""
        print("Voice activity detected! Add your custom logic here.")
        # This is where you can add your custom logic
        
    def reset_status(self):
        """Reset status after voice detection"""
        if self.is_recording:
            self.status_label.setText("Listening for voice...")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Voice Activity Detection Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Create and set central widget
        self.voice_detector = VoiceDetectionWidget()
        self.setCentralWidget(self.voice_detector)
        
    def closeEvent(self, event):
        """Clean up when window is closed"""
        # Stop audio processing
        self.voice_detector.audio_processor.stop()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
