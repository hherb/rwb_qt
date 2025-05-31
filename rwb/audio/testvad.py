#!/usr/bin/env python
"""Voice Activity Detection and Speech-to-Text Testing Module.

This module connects the voice activity detector with the speech-to-text engine
to transcribe detected speech segments in real-time.
"""

import sys
import os
import numpy as np
import torch
import threading
import time
import queue
import pyaudio
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QPushButton, QLabel, QWidget, QProgressBar)
from PySide6.QtCore import QTimer, Signal, Slot, QObject

# Adjust imports based on how the script is run
if __name__ == '__main__':
    # When run directly as a script
    # Get the path to qtrwb directory (project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
    sys.path.insert(0, project_root)
    
    # Import directly from the local directory
    from pyvoicedetector import VoiceActivityDetector
    from stt import SpeechToText
else:
    # When imported as a module
    from .pyvoicedetector import VoiceActivityDetector
    from .stt import SpeechToText

from fastrtc import get_stt_model


class AudioCapture:
    """Records and manages audio data for voice detection and transcription."""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """Initialize audio capture.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Size of audio chunks to process
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.format = pyaudio.paFloat32
        self.channels = 1
        
        # Audio recording components
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Buffer to store audio data for processing
        self.buffer = np.array([], dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.buffer_max_seconds = 30  # Maximum buffer size (seconds)
        self.max_buffer_size = self.sample_rate * self.buffer_max_seconds
        
        # State management
        self.is_recording = False
        self.is_running = True  # Used to control the background thread
    
    def start_capture(self):
        """Start capturing audio."""
        if self.stream is not None:
            return
        
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            self.is_recording = True
            print("Audio capture started.")
        except Exception as e:
            print(f"Error starting audio capture: {e}")
    
    def stop_capture(self):
        """Stop capturing audio."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        print("Audio capture stopped.")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process incoming audio data."""
        if not self.is_recording:
            return (None, pyaudio.paComplete)
        
        # Convert the raw audio data to a numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Add the new data to our buffer with thread safety
        with self.buffer_lock:
            self.buffer = np.append(self.buffer, audio_data)
            
            # Trim the buffer if it gets too large
            if len(self.buffer) > self.max_buffer_size:
                self.buffer = self.buffer[-self.max_buffer_size:]
        
        return (in_data, pyaudio.paContinue)
    
    def get_audio_chunk(self, seconds: float) -> np.ndarray:
        """Get a chunk of audio from the buffer.
        
        Args:
            seconds: Number of seconds of audio to retrieve
            
        Returns:
            np.ndarray: Audio data
        """
        samples = int(self.sample_rate * seconds)
        with self.buffer_lock:
            if len(self.buffer) >= samples:
                return self.buffer[-samples:]
            else:
                # Return whatever we have if we don't have enough
                return self.buffer.copy()
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        with self.buffer_lock:
            self.buffer = np.array([], dtype=np.float32)
    
    def cleanup(self):
        """Release all resources."""
        self.is_running = False
        self.stop_capture()
        self.audio.terminate()


class VADTranscriber(QObject):
    """Combines VAD and STT to transcribe speech when voice activity is detected."""
    
    # Signal to notify when new transcription is ready
    transcription_ready = Signal(str)
    # Signal for audio level visualization
    audio_level = Signal(float)
    # Signal for VAD state changes
    vad_state_changed = Signal(bool)  # True = speech detected, False = silence
    
    def __init__(self, vad_threshold: float = 0.3, vad_window: float = 1.0, 
                 sample_rate: int = 16000):
        """Initialize VAD transcriber.
        
        Args:
            vad_threshold: Threshold for VAD (0.0-1.0)
            vad_window: Time window in seconds to check for voice activity
            sample_rate: Audio sample rate in Hz
        """
        super().__init__()
        self.vad_threshold = vad_threshold
        self.vad_window = vad_window
        self.sample_rate = sample_rate
        
        # Initialize components
        self.audio_capture = AudioCapture(sample_rate=sample_rate)
        self.vad = VoiceActivityDetector(threshold=vad_threshold, sampling_rate=sample_rate)
        
        # Load STT model with more verbose output
        print("Loading Speech-to-Text model...")
        try:
            print("INFO:   Initializing STT model - this might take a moment...")
            self.stt_model = get_stt_model()
            print(f"STT model loaded successfully: {type(self.stt_model)}")
            
            # Warm up the STT model with a small sample to avoid cold-start issues
            dummy_audio = np.zeros((1, sample_rate), dtype=np.float32)
            print("INFO:   Warming up STT model...")
            self.stt_model.stt((sample_rate, dummy_audio))
            print("INFO:   STT model warmed up.")
        except Exception as e:
            print(f"Error loading STT model: {e}")
            import traceback
            traceback.print_exc()
            raise
            
        self.stt = SpeechToText(self.stt_model)
        print("VAD Transcriber initialized successfully")
        
        # Processing state
        self.is_running = False
        self.processing_thread = None
        self.speech_detected = False
        self.speech_buffer = np.array([], dtype=np.float32)
        self.speech_timeout = 0.8  # Seconds of silence before processing speech
        self.last_speech_time = 0
        self.min_speech_length = 0.8  # Minimum length of speech to process (seconds)
        
        # For preventing duplicate or too frequent transcriptions
        self.last_transcription = ""
        self.last_transcription_time = 0
        self.min_transcription_interval = 2.0  # Minimum seconds between transcriptions
        
        # Audio level calculation
        self.level_update_interval = 0.1  # Seconds
        self.last_level_update = 0
    
    def start(self):
        """Start VAD and transcription processing."""
        if self.is_running:
            return
        
        self.is_running = True
        self.audio_capture.start_capture()
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        print("VAD Transcriber started.")
    
    def stop(self):
        """Stop VAD and transcription processing."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
            
        self.audio_capture.stop_capture()
        print("VAD Transcriber stopped.")
    
    def _process_loop(self):
        """Main processing loop for VAD and transcription."""
        # Buffer to store recent audio for pre-speech context
        context_buffer = np.array([], dtype=np.float32)
        context_size = int(self.sample_rate * 0.5)  # 0.5 seconds of context
        
        consecutive_speech_frames = 0
        consecutive_silence_frames = 0
        min_consecutive_speech = 3  # Require 3 consecutive positive frames to start speech
        
        while self.is_running:
            try:
                # Get audio chunk for VAD analysis
                audio_chunk = self.audio_capture.get_audio_chunk(self.vad_window)
                
                # Skip processing if we don't have enough audio
                if len(audio_chunk) < self.sample_rate * 0.3:  # At least 0.3 seconds
                    time.sleep(0.1)
                    continue
                
                # Update audio level for visualization
                current_time = time.time()
                if current_time - self.last_level_update > self.level_update_interval:
                    level = np.sqrt(np.mean(np.square(audio_chunk[-self.sample_rate//10:])))
                    self.audio_level.emit(level)
                    self.last_level_update = current_time
                
                # Update context buffer
                if len(context_buffer) > context_size:
                    context_buffer = context_buffer[-context_size:]
                context_buffer = np.append(context_buffer, audio_chunk[-self.sample_rate//4:])
                
                # Check for voice activity
                is_speech = self.vad.is_speech(audio_chunk)
                
                # Count consecutive speech/silence frames for more stable detection
                if is_speech:
                    consecutive_speech_frames += 1
                    consecutive_silence_frames = 0
                else:
                    consecutive_silence_frames += 1
                    consecutive_speech_frames = 0
                
                # Handle state transitions with more stability
                if consecutive_speech_frames >= min_consecutive_speech and not self.speech_detected:
                    # Transition from silence to speech
                    print("Voice detected!")
                    self.speech_detected = True
                    # Include context before the speech started
                    self.speech_buffer = np.array(context_buffer, dtype=np.float32)
                    self.last_speech_time = time.time()
                    self.vad_state_changed.emit(True)
                
                elif is_speech and self.speech_detected:
                    # Continuing speech - append to buffer
                    self.speech_buffer = np.append(self.speech_buffer, audio_chunk[-self.sample_rate//4:])
                    self.last_speech_time = time.time()
                
                elif consecutive_silence_frames >= 4 and self.speech_detected:
                    # Check if silence has persisted long enough to end the speech segment
                    if (time.time() - self.last_speech_time) > self.speech_timeout:
                        # Process the speech if it's long enough
                        if len(self.speech_buffer) > self.sample_rate * self.min_speech_length:
                            print(f"Processing speech segment ({len(self.speech_buffer)/self.sample_rate:.1f} seconds)...")
                            self._process_speech()
                        
                        # Reset for next detection
                        self.speech_detected = False
                        self.speech_buffer = np.array([], dtype=np.float32)
                        self.vad_state_changed.emit(False)
                        consecutive_silence_frames = 0
                
                # Maximum speech buffer length to prevent memory issues (10 seconds)
                if len(self.speech_buffer) > self.sample_rate * 10:
                    print("Speech segment too long, processing now...")
                    self._process_speech()
                    self.speech_detected = False
                    self.speech_buffer = np.array([], dtype=np.float32)
                    self.vad_state_changed.emit(False)
                
                # Sleep briefly to reduce CPU usage
                time.sleep(0.03)
                
            except Exception as e:
                print(f"Error in processing loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)  # Sleep longer after an error
    
    def _process_speech(self):
        """Process detected speech with STT."""
        try:
            # Ensure we have data to process
            if len(self.speech_buffer) == 0:
                return
            
            # Check if enough time has passed since last transcription
            current_time = time.time()
            if current_time - self.last_transcription_time < self.min_transcription_interval:
                print("Skipping transcription - too soon after previous transcription")
                return
            
            print(f"Processing audio data length: {len(self.speech_buffer)} samples, {len(self.speech_buffer)/self.sample_rate:.2f} seconds")
            
            # For very long segments, split them into smaller chunks that the model can handle better
            # Most STT models work better with 5-10 second chunks
            max_chunk_length = 8 * self.sample_rate  # 8 seconds per chunk
            
            if len(self.speech_buffer) > max_chunk_length:
                print("Speech segment too long, splitting into chunks...")
                chunks = []
                # Split with slight overlap (0.5 second) between chunks
                overlap = int(0.5 * self.sample_rate)
                
                for i in range(0, len(self.speech_buffer), max_chunk_length - overlap):
                    chunk_end = min(i + max_chunk_length, len(self.speech_buffer))
                    chunks.append(self.speech_buffer[i:chunk_end])
                    if chunk_end == len(self.speech_buffer):
                        break
                
                # Process each chunk and combine results
                all_texts = []
                for i, chunk in enumerate(chunks):
                    print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)/self.sample_rate:.2f} seconds)...")
                    result = self._process_audio_chunk(chunk)
                    if result:
                        all_texts.append(result)
                
                # Combine all results
                if all_texts:
                    combined_text = " ".join(all_texts)
                    cleaned_text = self._clean_transcript(combined_text)
                    
                    print(f"Combined transcription: {cleaned_text}")
                    self.last_transcription = cleaned_text
                    self.last_transcription_time = current_time
                    self.transcription_ready.emit(cleaned_text)
                else:
                    print("No transcription result from any chunk.")
            else:
                # Process as a single chunk for shorter segments
                result = self._process_audio_chunk(self.speech_buffer)
                if result:
                    print(f"Transcription: {result}")
                    self.last_transcription = result
                    self.last_transcription_time = current_time
                    self.transcription_ready.emit(result)
                
        except Exception as e:
            print(f"Error in speech processing: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_audio_chunk(self, audio_chunk):
        """Process a single chunk of audio data.
        
        Args:
            audio_chunk: The audio data to process
            
        Returns:
            str: The cleaned transcription text or empty string
        """
        try:
            print(f"Processing audio chunk: shape={audio_chunk.shape if hasattr(audio_chunk, 'shape') else 'unknown'}")
            
            # Save audio to a temporary WAV file - this is the method that worked in our test
            temp_filename = f"temp_speech_{int(time.time())}.wav"
            print(f"Saving audio to temporary file: {temp_filename}")
            
            try:
                import wave
                
                # Normalize audio if needed
                max_val = np.max(np.abs(audio_chunk))
                if max_val > 0:
                    normalized_audio = audio_chunk / max_val * 0.9
                else:
                    normalized_audio = audio_chunk
                
                # Convert to int16 format for WAV file (which is the format that worked in our test)
                audio_int16 = (normalized_audio * 32767).astype(np.int16)
                
                # Write to WAV file
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 2 bytes for int16
                    wf.setframerate(self.sample_rate)  # Sample rate
                    wf.writeframes(audio_int16.tobytes())
                
                # Read back the WAV file - this is exactly what worked in our test
                with wave.open(temp_filename, 'rb') as wf:
                    # Get basic info
                    sample_rate = wf.getframerate()
                    sample_width = wf.getsampwidth()
                    channels = wf.getnchannels()
                    
                    # Read all frames
                    raw_data = wf.readframes(wf.getnframes())
                    
                    # Convert to appropriate numpy format
                    audio_data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Reshape for the STT model
                    audio_data = audio_data.reshape(1, -1)
                    
                # Print info about the processed audio
                print(f"Processed audio: shape={audio_data.shape}, rate={sample_rate}, dtype={audio_data.dtype}")
                print(f"Audio stats: min={np.min(audio_data):.3f}, max={np.max(audio_data):.3f}, mean={np.mean(audio_data):.3f}")
                
                # Call STT model directly using the same format that worked in our test
                print("Calling STT model with WAV file data...")
                text = self.stt_model.stt((sample_rate, audio_data))
                print(f"STT result: {repr(text)}")
                
                # Remove temporary file
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file: {e}")
            
            except Exception as e:
                print(f"Error processing audio with WAV file method: {e}")
                import traceback
                traceback.print_exc()
                
                # Fall back to original method if WAV approach fails
                print("Falling back to direct audio processing method...")
                
                # 1. Normalize audio levels (ensure -1.0 to 1.0 range)
                max_val = np.max(np.abs(audio_chunk))
                if max_val > 0:
                    normalized_audio = audio_chunk / max_val * 0.9
                else:
                    normalized_audio = audio_chunk
                
                # 2. Prepare audio for STT - with added padding
                padding = np.zeros(int(self.sample_rate * 0.3), dtype=np.float32)
                padded_audio = np.concatenate([padding, normalized_audio, padding])
                
                if len(padded_audio.shape) == 1:
                    audio_data = padded_audio.reshape(1, -1)
                else:
                    audio_data = padded_audio
                
                print(f"Direct processing: shape={audio_data.shape}, rate={self.sample_rate}")
                
                # Call STT model directly
                text = self.stt_model.stt((self.sample_rate, audio_data))
            
            if text and text.strip():
                # Clean up the text - remove repeated words and segments
                cleaned_text = self._clean_transcript(text)
                
                # Only process if the cleaned text is still meaningful
                if cleaned_text and len(cleaned_text) >= 2:
                    return cleaned_text
                else:
                    print("Transcription too short after cleaning")
            else:
                print("No transcription result for this chunk.")
                
            return ""
                
        except Exception as e:
            print(f"Error processing audio chunk: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    def _clean_transcript(self, text: str) -> str:
        """Clean up transcript text by removing repetitions and noise.
        
        Args:
            text: The raw transcript text
            
        Returns:
            str: The cleaned transcript text
        """
        if not text:
            return ""
        
        # Convert to lowercase for better pattern matching
        text = text.strip()
        
        # Remove common repetition patterns
        
        # Split into words
        words = text.split()
        
        # Remove repetitive number sequences (like "1010, 1010, 1010")
        clean_words = []
        number_pattern = False
        prev_word = None
        
        for word in words:
            # Skip if it's a repetition of the previous word
            if word == prev_word:
                continue
                
            # Detect repetitive number patterns
            if word.isdigit() and prev_word and prev_word.isdigit():
                if not number_pattern:
                    clean_words.append(word)
                    number_pattern = True
            else:
                number_pattern = False
                clean_words.append(word)
                
            prev_word = word
        
        # Remove repetitive phrases with more than 3 consecutive repeated words
        # This handles cases like "is is is is mentioned"
        filtered_words = []
        repetition_count = 1
        
        for i in range(len(clean_words)):
            if i > 0 and clean_words[i] == clean_words[i-1]:
                repetition_count += 1
            else:
                if repetition_count <= 2:  # Allow up to 2 repetitions (like "yes yes")
                    # Add any legitimate repetitions back
                    for _ in range(repetition_count):
                        if i > 0:
                            filtered_words.append(clean_words[i-1])
                else:
                    # Just add one instance of heavily repeated words
                    filtered_words.append(clean_words[i-1])
                    
                repetition_count = 1
        
        # Handle the last word
        if repetition_count <= 2:
            for _ in range(repetition_count):
                if clean_words:
                    filtered_words.append(clean_words[-1])
        else:
            if clean_words:
                filtered_words.append(clean_words[-1])
        
        # Join the words back into a string
        cleaned_text = " ".join(filtered_words)
        
        return cleaned_text
    
    def cleanup(self):
        """Release all resources."""
        self.stop()
        if self.audio_capture:
            self.audio_capture.cleanup()


class VADTranscriberUI(QMainWindow):
    """Simple UI for the VAD and STT demonstration."""
    
    def __init__(self):
        """Initialize the UI."""
        super().__init__()
        
        self.setWindowTitle("Voice Detection & Transcription Test")
        self.setGeometry(100, 100, 500, 300)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Create audio level indicator
        self.level_bar = QProgressBar()
        self.level_bar.setMinimum(0)
        self.level_bar.setMaximum(100)
        layout.addWidget(self.level_bar)
        
        # Create transcription output label
        self.output_label = QLabel("Waiting for voice...")
        self.output_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; min-height: 100px;")
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)
        
        # Create Start/Stop button
        self.toggle_button = QPushButton("Start Listening")
        self.toggle_button.clicked.connect(self.toggle_listening)
        layout.addWidget(self.toggle_button)
        
        # Initialize the VAD transcriber
        self.transcriber = VADTranscriber(vad_threshold=0.5)
        self.transcriber.transcription_ready.connect(self.update_transcription)
        self.transcriber.audio_level.connect(self.update_audio_level)
        self.transcriber.vad_state_changed.connect(self.update_vad_state)
        
        # Track listening state
        self.is_listening = False
    
    def toggle_listening(self):
        """Toggle between listening and not listening states."""
        if not self.is_listening:
            self.transcriber.start()
            self.toggle_button.setText("Stop Listening")
            self.status_label.setText("Listening for voice...")
            self.is_listening = True
        else:
            self.transcriber.stop()
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
        # Scale level to progress bar range (0-100)
        scaled_level = min(int(level * 500), 100)
        self.level_bar.setValue(scaled_level)
    
    @Slot(bool)
    def update_vad_state(self, is_speech):
        """Update UI based on VAD state changes."""
        if is_speech:
            self.status_label.setText("Voice detected! 🎤")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.status_label.setText("Listening for voice...")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    
    def closeEvent(self, event):
        """Clean up resources when closing the window."""
        self.transcriber.cleanup()
        event.accept()


def main():
    """Run the VAD transcriber application."""
    app = QApplication(sys.argv)
    window = VADTranscriberUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
