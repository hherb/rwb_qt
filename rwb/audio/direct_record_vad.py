#!/usr/bin/env python
"""Voice Activity Detector with Direct File Processing.

This script tests a hybrid approach that combines real-time voice detection
with temporary files to improve transcription reliability.
"""

import sys
import os
import numpy as np
import torch
import threading
import time
import wave
import pyaudio
from typing import Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QPushButton, QLabel, QWidget, QProgressBar)
from PySide6.QtCore import QTimer, Signal, Slot, QObject

# Adjust imports based on how the script is run
if __name__ == '__main__':
    # When run directly as a script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
    sys.path.insert(0, project_root)
    
    # Import directly from the local directory
    from pyvoicedetector import VoiceActivityDetector
    from stt import SpeechToText

from fastrtc import get_stt_model

class DirectRecordVAD(QObject):
    """Combines VAD with direct recording to WAV files for better transcription."""
    
    # Signal to notify when new transcription is ready
    transcription_ready = Signal(str)
    # Signal for audio level visualization
    audio_level = Signal(float)
    # Signal for VAD state changes
    vad_state_changed = Signal(bool)  # True = speech detected, False = silence
    
    def __init__(self, vad_threshold: float = 0.3):
        """Initialize the VAD and recording system."""
        super().__init__()
        
        # Audio parameters
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.format = pyaudio.paFloat32
        self.vad_window = 1.0  # seconds for VAD analysis
        
        # Initialize components
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.vad = VoiceActivityDetector(threshold=vad_threshold, sampling_rate=self.sample_rate)
        
        # Load STT model
        print("Loading Speech-to-Text model...")
        try:
            self.stt_model = get_stt_model()
            print(f"STT model loaded successfully: {type(self.stt_model)}")
            
            # Warm up the model
            dummy_audio = np.zeros((1, self.sample_rate), dtype=np.float32)
            self.stt_model.stt((self.sample_rate, dummy_audio))
            print("STT model warmed up.")
        except Exception as e:
            print(f"Error loading STT model: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Processing state
        self.is_running = False
        self.is_recording_speech = False
        self.audio_buffer = []
        self.processing_thread = None
        self.recording_filename = None
        self.recording_wav = None
        self.last_speech_time = 0
        self.speech_timeout = 1.0  # seconds of silence before stopping recording
        
        # For audio level visualization
        self.level_buffer = np.zeros(int(self.sample_rate / self.chunk_size * 0.2))  # 200ms buffer
        
        # For preventing duplicate transcriptions
        self.last_transcription = ""
        self.last_transcription_time = 0
        self.min_transcription_interval = 2.0  # seconds
    
    def start(self):
        """Start the VAD and recording system."""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_recording_speech = False
        
        # Start audio capture
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            print("Audio capture started.")
        except Exception as e:
            print(f"Error starting audio capture: {e}")
            self.is_running = False
            return
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        print("Voice detection started.")
    
    def stop(self):
        """Stop the VAD and recording system."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop recording if active
        if self.is_recording_speech:
            self._stop_recording()
        
        # Stop audio capture
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Wait for processing thread to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        print("Voice detection stopped.")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Handle incoming audio data from PyAudio."""
        if not self.is_running:
            return (None, pyaudio.paComplete)
        
        # Convert to numpy array for level calculation
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Calculate audio level (rolling RMS)
        self.level_buffer = np.roll(self.level_buffer, -1)
        self.level_buffer[-1] = np.sqrt(np.mean(np.square(audio_data)))
        level = np.mean(self.level_buffer)
        self.audio_level.emit(level)
        
        # If we're currently recording speech, add the data to our buffer
        if self.is_recording_speech and self.recording_wav:
            try:
                # Convert float32 to int16 for WAV file
                audio_int16 = (audio_data * 32767).astype(np.int16)
                self.recording_wav.writeframes(audio_int16.tobytes())
            except Exception as e:
                print(f"Error writing audio data: {e}")
        
        # Keep a copy of the raw audio data for VAD analysis
        self.audio_buffer.append(audio_data.copy())
        buffer_length = self.vad_window * self.sample_rate / self.chunk_size
        if len(self.audio_buffer) > buffer_length:
            self.audio_buffer.pop(0)
        
        return (in_data, pyaudio.paContinue)
    
    def _process_loop(self):
        """Main processing loop for voice detection."""
        consecutive_speech = 0
        consecutive_silence = 0
        min_speech_frames = 3  # Number of consecutive frames needed to start recording
        
        speech_start_time = 0
        max_recording_time = 10.0  # seconds
        
        while self.is_running:
            try:
                # Wait for enough audio data
                if len(self.audio_buffer) < int(self.vad_window * self.sample_rate / self.chunk_size * 0.75):
                    time.sleep(0.1)
                    continue
                
                # Concatenate audio chunks for VAD analysis
                audio_concat = np.concatenate(self.audio_buffer)
                
                # Check for voice activity
                is_speech = self.vad.is_speech(audio_concat)
                
                if is_speech:
                    consecutive_speech += 1
                    consecutive_silence = 0
                else:
                    consecutive_silence += 1
                    consecutive_speech = 0
                
                # Start recording when speech is detected
                if consecutive_speech >= min_speech_frames and not self.is_recording_speech:
                    self._start_recording()
                    speech_start_time = time.time()
                    self.vad_state_changed.emit(True)
                
                # Keep track of the last time we heard speech
                if is_speech and self.is_recording_speech:
                    self.last_speech_time = time.time()
                
                # Stop recording after a period of silence
                if self.is_recording_speech:
                    current_time = time.time()
                    
                    # Check for timeout conditions
                    if consecutive_silence >= 5 and (current_time - self.last_speech_time) > self.speech_timeout:
                        print("Speech ended due to silence.")
                        self._stop_recording()
                        self._process_recording()
                        self.vad_state_changed.emit(False)
                    
                    # Check for maximum recording time
                    elif (current_time - speech_start_time) > max_recording_time:
                        print("Maximum recording time reached.")
                        self._stop_recording()
                        self._process_recording()
                        self.vad_state_changed.emit(False)
                
                # Sleep to reduce CPU usage
                time.sleep(0.05)
            
            except Exception as e:
                print(f"Error in processing loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)
    
    def _start_recording(self):
        """Start recording speech to a WAV file."""
        if self.is_recording_speech:
            return
        
        # Create a unique filename
        self.recording_filename = f"speech_{int(time.time())}.wav"
        print(f"Voice detected! Recording to {self.recording_filename}")
        
        try:
            self.recording_wav = wave.open(self.recording_filename, 'wb')
            self.recording_wav.setnchannels(self.channels)
            self.recording_wav.setsampwidth(2)  # 2 bytes for int16
            self.recording_wav.setframerate(self.sample_rate)
            self.is_recording_speech = True
            self.last_speech_time = time.time()
            
            # Also write any buffered audio that might contain the start of speech
            for audio_chunk in self.audio_buffer:
                audio_int16 = (audio_chunk * 32767).astype(np.int16)
                self.recording_wav.writeframes(audio_int16.tobytes())
        
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording_speech = False
            self.recording_filename = None
            self.recording_wav = None
    
    def _stop_recording(self):
        """Stop recording speech."""
        if not self.is_recording_speech:
            return
        
        try:
            if self.recording_wav:
                self.recording_wav.close()
        except Exception as e:
            print(f"Error closing WAV file: {e}")
        
        self.is_recording_speech = False
        self.recording_wav = None
    
    def _process_recording(self):
        """Process a completed recording."""
        if not self.recording_filename or not os.path.exists(self.recording_filename):
            print("No recording file to process.")
            return
        
        print(f"Processing recording: {self.recording_filename}")
        
        try:
            # Open the WAV file
            with wave.open(self.recording_filename, 'rb') as wf:
                # Get file info
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = n_frames / sample_rate
                
                print(f"Processing {duration:.1f} seconds of audio, {n_frames} frames")
                
                # Skip very short recordings (less than 0.5 seconds)
                if duration < 0.5:
                    print("Recording too short, skipping.")
                    return
                
                # Read all frames
                raw_data = wf.readframes(n_frames)
                
                # Convert to numpy array
                if sample_width == 2:  # 16-bit audio
                    audio_data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                else:
                    print(f"Unsupported sample width: {sample_width}")
                    return
                
                # Reshape audio data for the STT model
                audio_data = audio_data.reshape(1, -1)
                
                print(f"Audio data shape: {audio_data.shape}, dtype: {audio_data.dtype}")
                print(f"Audio stats: min={np.min(audio_data):.3f}, max={np.max(audio_data):.3f}, mean={np.mean(audio_data):.3f}")
                
                # Pass to STT model
                print("Sending audio to STT model...")
                text = self.stt_model.stt((sample_rate, audio_data))
                print(f"STT result: {repr(text)}")
                
                # Check if we got a valid transcription
                if text and text.strip():
                    current_time = time.time()
                    
                    # Only emit if it's been long enough since the last transcription
                    if current_time - self.last_transcription_time > self.min_transcription_interval:
                        # Clean up the text (remove repetitions, etc.)
                        cleaned_text = self._clean_transcript(text)
                        
                        if cleaned_text:
                            print(f"Final transcription: {cleaned_text}")
                            self.transcription_ready.emit(cleaned_text)
                            self.last_transcription = cleaned_text
                            self.last_transcription_time = current_time
                        else:
                            print("Transcription filtered out during cleaning.")
                    else:
                        print("Transcription too soon after previous one, skipping.")
                else:
                    print("No transcription result.")
            
            # Remove the temporary file
            try:
                os.remove(self.recording_filename)
                print(f"Temporary file {self.recording_filename} removed.")
            except Exception as e:
                print(f"Error removing temporary file: {e}")
            
        except Exception as e:
            print(f"Error processing recording: {e}")
            import traceback
            traceback.print_exc()
    
    def _clean_transcript(self, text: str) -> str:
        """Clean up transcript by removing repetitions, etc."""
        if not text:
            return ""
            
        # Basic cleaning - strip whitespace
        cleaned_text = text.strip()
        
        # Split into words
        words = cleaned_text.split()
        
        # Remove consecutive repeated words
        result = []
        prev_word = None
        
        for word in words:
            if word != prev_word:
                result.append(word)
            prev_word = word
        
        return " ".join(result)


class DirectRecordVADUI(QMainWindow):
    """Simple UI for the direct recording VAD system."""
    
    def __init__(self):
        """Initialize the UI."""
        super().__init__()
        
        self.setWindowTitle("Direct Recording Voice Detection & Transcription")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Create audio level indicator
        self.level_bar = QProgressBar()
        self.level_bar.setMinimum(0)
        self.level_bar.setMaximum(100)
        layout.addWidget(self.level_bar)
        
        # Create transcription output
        self.output_label = QLabel("Waiting for speech...")
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; min-height: 200px;")
        layout.addWidget(self.output_label)
        
        # Create start/stop button
        self.toggle_button = QPushButton("Start Listening")
        self.toggle_button.clicked.connect(self.toggle_listening)
        layout.addWidget(self.toggle_button)
        
        # Initialize the VAD recorder
        self.vad_recorder = DirectRecordVAD(vad_threshold=0.4)
        self.vad_recorder.transcription_ready.connect(self.update_transcription)
        self.vad_recorder.audio_level.connect(self.update_audio_level)
        self.vad_recorder.vad_state_changed.connect(self.update_vad_state)
        
        # Listening state
        self.is_listening = False
    
    def toggle_listening(self):
        """Toggle between listening and not listening states."""
        if not self.is_listening:
            self.vad_recorder.start()
            self.toggle_button.setText("Stop Listening")
            self.status_label.setText("Listening for voice...")
            self.is_listening = True
        else:
            self.vad_recorder.stop()
            self.toggle_button.setText("Start Listening")
            self.status_label.setText("Ready")
            self.is_listening = False
    
    @Slot(str)
    def update_transcription(self, text):
        """Update the UI with a new transcription."""
        self.output_label.setText(text)
    
    @Slot(float)
    def update_audio_level(self, level):
        """Update the audio level indicator."""
        level_percent = min(int(level * 500), 100)
        self.level_bar.setValue(level_percent)
    
    @Slot(bool)
    def update_vad_state(self, is_speech):
        """Update the UI based on speech detection."""
        if is_speech:
            self.status_label.setText("Voice detected! 🎤")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.status_label.setText("Listening for voice...")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    
    def closeEvent(self, event):
        """Clean up resources when the window is closed."""
        self.vad_recorder.stop()
        event.accept()


def main():
    """Run the direct recording VAD application."""
    app = QApplication(sys.argv)
    window = DirectRecordVADUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
