import sys
import os
import numpy as np
import torch
import queue
import threading
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QPushButton, QLabel, QWidget, QProgressBar,
                              QComboBox, QHBoxLayout, QSlider)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject
from typing import Callable, Optional

# Import aiortc for WebRTC audio capture
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaRecorder, MediaPlayer
import av


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


class AudioTrackProcessor(MediaStreamTrack):
    """Process audio track from WebRTC and run through VAD"""
    
    kind = "audio"  # This is an audio track
    
    def __init__(self, track, queue):
        super().__init__()
        self.track = track
        self.queue = queue
        
    async def recv(self):
        # Get the next frame from the track
        frame = await self.track.recv()
        
        # Process the audio frame
        if frame and frame.format and frame.format.name == "s16":
            # Convert audio samples to numpy array
            audio_array = frame.to_ndarray()
            
            # Convert to float32 and normalize to -1.0 to 1.0
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # If stereo, convert to mono
            if audio_float.shape[1] > 1:
                audio_float = audio_float.mean(axis=1)
            else:
                audio_float = audio_float.flatten()
                
            # Add to processing queue
            try:
                self.queue.put_nowait(audio_float)
            except queue.Full:
                pass  # Queue is full, skip this frame
            
        # Return the frame unchanged
        return frame


class WebRTCAudioProcessor(QObject):
    """Audio processor using WebRTC for capture"""
    
    # Signal emitted when voice is detected
    voice_detected = Signal()
    
    # Signal for audio level for visualizing
    audio_level = Signal(float)
    
    def __init__(self, vad, callback: Optional[Callable] = None):
        super().__init__()
        self.vad = vad
        self.callback = callback
        
        # Processing state
        self.pc = None  # PeerConnection
        self.is_running = False
        self.audio_queue = queue.Queue(maxsize=100)
        self.processing_thread = None
        
    async def start_webrtc(self):
        """Start WebRTC audio capture"""
        # Create a new peer connection
        self.pc = RTCPeerConnection()
        
        # Create an audio track from the default microphone
        # Using "default" for the input device and "alsa" for the format on Linux
        # On macOS, we use "avfoundation" format and "0:none" for default mic (audio:video)
        import platform
        if platform.system() == "Darwin":  # macOS
            player = MediaPlayer("0:none", format="avfoundation", options={
                "audio_size": "stereo",
                "audio_rate": "16000"
            })
        elif platform.system() == "Linux":
            player = MediaPlayer("default", format="alsa", options={
                "audio_size": "stereo",
                "audio_rate": "16000"
            })
        else:  # Windows or other
            player = MediaPlayer("audio=default", format="dshow", options={
                "audio_size": "stereo",
                "audio_rate": "16000"
            })
        
        # Add local audio track
        self.pc.addTrack(player.audio)
        
        # Set up a data channel for signaling
        self.channel = self.pc.createDataChannel("audio")
        
        # Create an offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        
        # For the remote side, we'll just use the local description as the remote
        # This is just for testing purposes
        answer = RTCSessionDescription(
            sdp=offer.sdp.replace("sendrecv", "recvonly"),
            type="answer",
        )
        await self.pc.setRemoteDescription(answer)
        
        # Set up a processor for the received track
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "audio":
                processor = AudioTrackProcessor(track, self.audio_queue)
                self.pc.addTrack(processor)
                
    def start(self):
        """Start audio capture and processing"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start WebRTC in a separate thread
        threading.Thread(target=self._start_webrtc_thread).start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def _start_webrtc_thread(self):
        """Start WebRTC in a separate thread"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_webrtc())
        loop.run_forever()
        
    def stop(self):
        """Stop audio capture and processing"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop WebRTC in a separate thread
        if self.pc:
            threading.Thread(target=self._stop_webrtc_thread).start()
            
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
            
    def _stop_webrtc_thread(self):
        """Stop WebRTC in a separate thread"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.pc.close())
        
    def _process_audio(self):
        """Process audio data with VAD in a separate thread"""
        window_size = 5  # Number of chunks to analyze together (~320ms)
        audio_window = []
        
        while self.is_running:
            try:
                # Get audio chunk from queue
                audio_data = self.audio_queue.get(timeout=0.5)
                
                # Calculate audio level for visualization (RMS)
                level = np.sqrt(np.mean(np.square(audio_data)))
                self.audio_level.emit(level)
                
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
        
        # Sensitivity control
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("VAD Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(10)
        self.sensitivity_slider.setMaximum(90)
        self.sensitivity_slider.setValue(50)  # Default 0.5
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        layout.addLayout(sensitivity_layout)
        
        # Button to start/stop
        self.toggle_button = QPushButton("Start Listening")
        self.toggle_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.toggle_button)
        
        # Set layout
        self.setLayout(layout)
        
        # Initialize VAD
        self.vad = VoiceActivityDetector(threshold=0.5, sampling_rate=16000)
        
        # Initialize audio processor
        self.audio_processor = WebRTCAudioProcessor(self.vad, callback=self.on_voice_detected)
        self.audio_processor.voice_detected.connect(self.on_voice_signal)
        self.audio_processor.audio_level.connect(self.update_level)
        
        # Recording state
        self.is_recording = False
        
        # Timer to reset status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.reset_status)
        self.status_timer.setSingleShot(True)
        
    def update_sensitivity(self, value):
        """Update VAD sensitivity"""
        # Convert slider value (10-90) to threshold (0.9-0.1)
        # Lower threshold = higher sensitivity
        threshold = 1.0 - (value / 100.0)
        self.vad.threshold = threshold
        print(f"VAD sensitivity updated: {value}%, threshold: {threshold:.2f}")
        
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
        
        self.setWindowTitle("WebRTC Voice Activity Detection")
        self.setGeometry(100, 100, 500, 250)
        
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
