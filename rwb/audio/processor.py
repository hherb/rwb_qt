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
from rwb.agents.rwbagent import RWBAgent  # Updated import path


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
        tts_options: Any,
        agent: Optional[RWBAgent] = None  # Add agent parameter
    ):
        """Initialize the audio processor.
        
        Args:
            audio_data: The audio data to process, or None for text input
            sample_rate: The sample rate of the audio
            stt_model: The speech-to-text model
            tts_model: The text-to-speech model
            tts_options: Options for text-to-speech synthesis
            agent: RWBAgent for LLM inference (optional)
        """
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.tts_options = tts_options
        self.agent = agent or RWBAgent()  # Use provided agent or create a default one
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
                # Skip emitting text update for direct text input as the UI already shows it
                # This prevents duplication of user messages
            else:
                # Convert audio data to the format expected by the STT model
                if isinstance(self.audio_data, np.ndarray):
                    # If it's already a numpy array, ensure it's in the right shape
                    if len(self.audio_data.shape) == 1:
                        audio_data = self.audio_data.reshape(1, -1)
                    else:
                        audio_data = self.audio_data
                else:
                    # Convert bytes to numpy array
                    audio_data = np.frombuffer(self.audio_data, dtype=np.float32)
                    audio_data = audio_data.reshape(1, -1)
                
                # Convert to text
                user_text = self.stt_model.stt((self.sample_rate, audio_data))
                
                # Only emit text update for speech input, not for direct text
                self.text_update.emit(f"{self.current_message_id}_user", user_text)
            
            # Get LLM response with streaming
            assistant_text = ""
            current_sentence = ""
            output_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            
            try:
                # Use the agent to stream responses
                for chunk in self.agent.astream(user_text):
                    assistant_text += chunk
                    current_sentence += chunk
                    
                    # Emit streaming text update
                    self.text_update.emit(f"{self.current_message_id}_assistant", assistant_text)
                    
                    # Check if we have a complete sentence
                    # Look for sentence boundaries that are followed by a space or end of text
                    sentence_end = False
                    for end in ('.', '!', '?'):
                        if end in current_sentence:
                            # Check if the end is followed by a space or is at the end of the text
                            pos = current_sentence.rfind(end)
                            if pos == len(current_sentence) - 1 or current_sentence[pos + 1] == ' ':
                                sentence_end = True
                                break
                        
                    # Also consider the end of the response as a sentence boundary
                    if sentence_end  and current_sentence.strip():
                        # Process the current sentence for TTS
                        if current_sentence.strip():  # Only process if we have actual content
                            tts_stream = self.tts_model.stream_tts_sync(current_sentence.strip(), options=self.tts_options)
                            
                            # Process each chunk of TTS audio
                            for tts_chunk in tts_stream:
                                if isinstance(tts_chunk, tuple):
                                    if len(tts_chunk) > 0:
                                        sample_rate, audio_data = tts_chunk
                                        if isinstance(audio_data, np.ndarray):
                                            # Resample from Kokoro's rate to PyAudio's rate
                                            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
                                            audio_bytes = audio_data.tobytes()
                                            output_stream.write(audio_bytes)
                                else:
                                    if isinstance(tts_chunk, np.ndarray):
                                        audio_data = librosa.resample(tts_chunk, orig_sr=24000, target_sr=44100)
                                        audio_bytes = audio_data.tobytes()
                                        output_stream.write(audio_bytes)
                                    elif isinstance(tts_chunk, bytes):
                                        audio_array = np.frombuffer(tts_chunk, dtype=np.float32)
                                        audio_array = librosa.resample(audio_array, orig_sr=24000, target_sr=44100)
                                        audio_bytes = audio_array.tobytes()
                                        output_stream.write(audio_bytes)
                            
                            # Reset current sentence
                            current_sentence = ""
                
                # Emit the final results
                self.finished.emit(user_text, assistant_text)
                
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