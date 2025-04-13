"""Audio processing module.

This module provides the AudioProcessor class with separate methods for:
- Text-to-speech synthesis (TTS)
- Speech-to-text conversion (STT)
"""

import numpy as np
import pyaudio
import librosa
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QThreadPool
from typing import Optional, Any, Iterator, List, Dict, Tuple


class AudioProcessorSignals(QObject):
    """Signals for the audio processor worker."""
    started = Signal()
    finished = Signal()
    error = Signal(str)
    result = Signal(object)


class AudioProcessorWorker(QRunnable):
    """Worker for running audio processing tasks in a separate thread."""
    
    def __init__(self, fn, *args, **kwargs):
        """Initialize the worker.
        
        Args:
            fn: Function to run in the thread
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = AudioProcessorSignals()
        
    @Slot()
    def run(self):
        """Run the worker function in a separate thread."""
        try:
            self.signals.started.emit()
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class AudioProcessor(QObject):
    """Handles audio processing with separate methods for TTS and STT."""
    
    speaking = Signal()  # Signal for when speaking starts
    done_speaking = Signal()  # Signal for when speaking ends
    stt_completed = Signal(str)  # Signal emitted when STT is complete
    error = Signal(str)  # Signal for errors
    
    def __init__(
        self,
        stt_model: Any,
        tts_model: Any,
        tts_options: Any = None
    ):
        """Initialize the audio processor.
        
        Args:
            stt_model: The speech-to-text model
            tts_model: The text-to-speech model
            tts_options: Options for text-to-speech synthesis (optional)
        """
        super().__init__()
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.tts_options = tts_options
        
        self.audio = pyaudio.PyAudio()
        self.is_speaking = False
        self.output_stream = None
        
        # Thread pool for background processing
        self.threadpool = QThreadPool()
        print(f"Audio processor using maximum {self.threadpool.maxThreadCount()} threads")
        
    def _tts_worker(self, text: str) -> None:
        """Worker function to perform TTS in a separate thread.
        
        Args:
            text: The text to convert to speech
        """
        try:
            # Set up audio output stream if needed
            if not self.output_stream or not self.output_stream.is_active():
                self.output_stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=44100,
                    output=True,
                    frames_per_buffer=1024
                )
            
            # Process the text for TTS
            tts_stream = self.tts_model.stream_tts_sync(text.strip(), options=self.tts_options)
            
            # Process each chunk of TTS audio
            for tts_chunk in tts_stream:
                if isinstance(tts_chunk, tuple):
                    if len(tts_chunk) > 0:
                        sample_rate, audio_data = tts_chunk
                        if isinstance(audio_data, np.ndarray):
                            # Resample from model's rate to PyAudio's rate
                            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
                            audio_bytes = audio_data.tobytes()
                            self.output_stream.write(audio_bytes)
                else:
                    if isinstance(tts_chunk, np.ndarray):
                        audio_data = librosa.resample(tts_chunk, orig_sr=24000, target_sr=44100)
                        audio_bytes = audio_data.tobytes()
                        self.output_stream.write(audio_bytes)
                    elif isinstance(tts_chunk, bytes):
                        audio_array = np.frombuffer(tts_chunk, dtype=np.float32)
                        audio_array = librosa.resample(audio_array, orig_sr=24000, target_sr=44100)
                        audio_bytes = audio_array.tobytes()
                        self.output_stream.write(audio_bytes)
        except Exception as e:
            self.error.emit(f"TTS error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def tts(self, text: str) -> None:
        """Convert text to speech and play it in a separate thread.
        
        Args:
            text: The text to convert to speech
        """
        if not text.strip():
            return
            
        self.speaking.emit()
        self.is_speaking = True
        
        # Create a worker to process TTS in a separate thread
        worker = AudioProcessorWorker(self._tts_worker, text)
        
        # Connect signals
        worker.signals.finished.connect(self._on_tts_finished)
        worker.signals.error.connect(self._on_tts_error)
        
        # Execute the worker
        self.threadpool.start(worker)
    
    def _on_tts_finished(self) -> None:
        """Handle completion of TTS processing."""
        self.is_speaking = False
        self.done_speaking.emit()
    
    def _on_tts_error(self, error: str) -> None:
        """Handle TTS processing error.
        
        Args:
            error: The error message
        """
        self.error.emit(f"TTS error: {error}")
        self.is_speaking = False
        self.done_speaking.emit()
    
    def _stt_worker(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Worker function to perform STT in a separate thread.
        
        Args:
            audio_data: The audio data to process
            sample_rate: The sample rate of the audio
            
        Returns:
            str: The transcribed text
        """
        try:
            # Convert audio data to the format expected by the STT model
            if isinstance(audio_data, np.ndarray):
                # If it's already a numpy array, ensure it's in the right shape
                if len(audio_data.shape) == 1:
                    audio_data = audio_data.reshape(1, -1)
            else:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(audio_data, dtype=np.float32)
                audio_data = audio_data.reshape(1, -1)
            
            # Convert to text
            text = self.stt_model.stt((sample_rate, audio_data))
            return text
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
    
    def process_audio_to_text(self, audio_data: np.ndarray, sample_rate: int) -> None:
        """Convert audio data to text using the STT model in a separate thread.
        
        Args:
            audio_data: The audio data to process
            sample_rate: The sample rate of the audio
        """
        # Create a worker to process STT in a separate thread
        worker = AudioProcessorWorker(self._stt_worker, audio_data, sample_rate)
        
        # Connect signals
        worker.signals.result.connect(self._on_stt_result)
        worker.signals.error.connect(self._on_stt_error)
        
        # Execute the worker
        self.threadpool.start(worker)
    
    def _on_stt_result(self, text: str) -> None:
        """Handle STT result.
        
        Args:
            text: The transcribed text
        """
        self.stt_completed.emit(text)
    
    def _on_stt_error(self, error: str) -> None:
        """Handle STT processing error.
        
        Args:
            error: The error message
        """
        self.error.emit(f"STT error: {error}")
    
    def close(self) -> None:
        """Close audio resources."""
        if self.output_stream and self.output_stream.is_active():
            self.output_stream.stop_stream()
            self.output_stream.close()
        
        if self.audio:
            self.audio.terminate()