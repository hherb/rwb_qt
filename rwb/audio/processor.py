"""Audio processing module.

This module handles the audio processing pipeline including:
- Speech-to-text conversion
- Text generation
- Text-to-speech synthesis
"""

import numpy as np
import pyaudio
import librosa
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal, Slot
from typing import Optional, Any, Tuple
from ollama import chat

class AudioProcessor(QThread):
    """Thread for processing audio asynchronously.
    
    This class handles the processing of audio data in a separate thread,
    including speech-to-text conversion, text generation, and text-to-speech
    synthesis.
    
    Signals:
        finished (Signal[str, str]): Emitted when processing is complete
            with user_text and assistant_text
        error (Signal[str]): Emitted when an error occurs
        speaking (Signal): Emitted when speaking starts
        done_speaking (Signal): Emitted when speaking ends
        text_update (Signal[str, str]): Emitted when new text is available
            (message_id, text)
    """
    
    finished = Signal(str, str)  # Signal for when processing is complete (user_text, assistant_text)
    error = Signal(str)  # Signal for errors
    speaking = Signal()  # Signal for when speaking starts
    done_speaking = Signal()  # Signal for when speaking ends
    text_update = Signal(str, str)  # Signal for text updates (message_id, text)
    
    def __init__(
        self,
        audio_data: Optional[np.ndarray],
        sample_rate: int,
        stt_model: Any,
        tts_model: Any,
        tts_options: Any
    ):
        """Initialize the audio processor.
        
        Args:
            audio_data: The audio data to process, or None for text input
            sample_rate: The sample rate of the audio
            stt_model: The speech-to-text model
            tts_model: The text-to-speech model
            tts_options: Options for text-to-speech synthesis
        """
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.tts_options = tts_options
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.audio = pyaudio.PyAudio()
        self.direct_text: Optional[str] = None
        self.current_message_id: Optional[str] = None
        
    def start(self, direct_text: Optional[str] = None) -> None:
        """Start the processor with optional direct text input.
        
        Args:
            direct_text: Optional text input to process directly
        """
        self.direct_text = direct_text
        self.current_message_id = str(id(self))  # Generate a unique ID for this message
        super().start()
        
    def run(self) -> None:
        """Process the audio data or direct text input.
        
        This method runs in a separate thread and handles:
        1. Converting audio to text (if audio provided) or using direct text
        2. Generating a response
        3. Converting the response to speech
        4. Playing the speech
        """
        try:
            # Get user text from audio or direct input
            if self.direct_text is not None:
                user_text = self.direct_text
            else:
                user_text = self.stt_model.stt((self.sample_rate, self.audio_data))
            
            # Emit user text update
            self.text_update.emit(f"{self.current_message_id}_user", user_text)
            
            # Get LLM response
            response = chat(model='granite3.2:8b-instruct-q8_0', messages=[
                {
                    'role': 'user',
                    'content': user_text,
                },
            ])
            
            assistant_text = response['message']['content']
            
            # Emit assistant text update
            self.text_update.emit(f"{self.current_message_id}_assistant", assistant_text)
            
            # Emit the final results
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