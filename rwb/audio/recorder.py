"""Audio recording module.

This module handles the audio recording functionality, including
starting/stopping recording and managing the audio stream.
"""

import pyaudio
import numpy as np
from PySide6.QtCore import QTimer
from typing import List, Optional

class AudioRecorder:
    """Handles audio recording functionality."""
    
    def __init__(self, chunk: int = 1024, format: int = pyaudio.paFloat32,
                 channels: int = 1, rate: int = 44100):
        """Initialize the audio recorder.
        
        Args:
            chunk: Size of audio chunks for recording
            format: Audio format (32-bit float)
            channels: Number of audio channels
            rate: Audio sample rate
        """
        self.CHUNK = chunk
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate
        
        self.recording = False
        self.frames: List[bytes] = []
        self.audio = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        self.record_timer: Optional[QTimer] = None
    
    def start_recording(self) -> None:
        """Start recording audio."""
        if not self.recording:
            self.recording = True
            self.frames = []
            
            try:
                # Get default input device index
                device_info = self.audio.get_default_input_device_info()
                device_index = device_info['index']
                
                # Open input stream with explicit device index
                self.input_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=self.CHUNK
                )
            except Exception as e:
                print(f"Error opening audio input stream: {e}")
                # Fall back to default device without explicit index
                try:
                    self.input_stream = self.audio.open(
                        format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK
                    )
                except Exception as e:
                    print(f"Failed to open audio input stream with fallback: {e}")
                    self.recording = False
                    return
            
            # Start recording timer
            self.record_timer = QTimer()
            self.record_timer.timeout.connect(self.record_audio)
            self.record_timer.start(10)  # Check every 10ms
    
    def record_audio(self) -> None:
        """Record a chunk of audio."""
        if self.recording and self.input_stream:
            try:
                data = self.input_stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                print(f"Error recording audio: {e}")
    
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the recorded audio data.
        
        Returns:
            numpy.ndarray: The recorded audio data
        """
        if self.recording:
            self.recording = False
            if self.record_timer:
                self.record_timer.stop()
            
            if self.input_stream and self.input_stream.is_active():
                try:
                    self.input_stream.stop_stream()
                    self.input_stream.close()
                except Exception as e:
                    print(f"Error stopping audio stream: {e}")
            
            # Convert audio to numpy array
            if self.frames:
                audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
                return audio_data.reshape(1, -1)
        
        return np.array([])
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.input_stream:
            self.input_stream.close()
        self.audio.terminate() 