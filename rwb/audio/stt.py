"""Speech-to-Text module.

This module provides a simple interface for speech-to-text conversion.
"""

import numpy as np
import threading
from typing import Any, Optional, Union
from fastrtc import get_stt_model


class SpeechToText:
    """A simple speech-to-text class to convert audio to text.
    
    This class provides an interface for speech recognition,
    converting audio data to text.
    """
    
    def __init__(self, stt_model: Any):
        """Initialize the SpeechToText engine.
        
        Args:
            stt_model: The speech-to-text model to use
        """
        self.stt_model = stt_model
        self.processing_cancelled = False
    
    def transcribe(self, audio_stream: Union[np.ndarray, bytes], sample_rate: int = 16000) -> str:
        """Convert audio data to text.
        
        Args:
            audio_stream: The audio data to process, can be numpy array or bytes
            sample_rate: The sample rate of the audio (default: 16000 Hz)
            
        Returns:
            str: The transcribed text
        """
        try:
            print(f"STT received audio: type={type(audio_stream)}, sample_rate={sample_rate}")
            
            # Check if processing was cancelled before starting
            if self.processing_cancelled:
                return ""
            
            # Convert audio data to the format expected by the STT model
            if isinstance(audio_stream, np.ndarray):
                # If it's already a numpy array, ensure it's in the right shape
                if len(audio_stream.shape) == 1:
                    audio_data = audio_stream.reshape(1, -1)
                    print(f"Reshaped 1D array to {audio_data.shape}")
                else:
                    audio_data = audio_stream
                    print(f"Using existing array shape {audio_data.shape}")
                    
                # Ensure data type is float32, which is typically required
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                    print(f"Converted data type to {audio_data.dtype}")
                    
                # Normalize if not already normalized
                max_val = np.max(np.abs(audio_data))
                if max_val > 1.0:
                    audio_data = audio_data / max_val
                    print(f"Normalized audio, max value was {max_val}")
            else:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(audio_stream, dtype=np.float32)
                audio_data = audio_data.reshape(1, -1)
                print(f"Converted bytes to numpy array with shape {audio_data.shape}")
            
            # Check again before heavy processing
            if self.processing_cancelled:
                return ""
            
            # Print info about the data we're sending to the STT model
            print(f"Sending to STT model: shape={audio_data.shape}, dtype={audio_data.dtype}, " +
                  f"min={np.min(audio_data):.2f}, max={np.max(audio_data):.2f}, " +
                  f"mean={np.mean(audio_data):.2f}")
            
            # Convert to text using the STT model
            print("Calling STT model...")
            text = self.stt_model.stt((sample_rate, audio_data))
            print(f"STT model returned: {repr(text)}")
            return text
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"STT error: {str(e)}")
            return ""
    
    def transcribe_async(self, audio_stream: Union[np.ndarray, bytes], sample_rate: int = 16000, 
                        callback: Optional[callable] = None) -> None:
        """Convert audio data to text asynchronously.
        
        Args:
            audio_stream: The audio data to process, can be numpy array or bytes
            sample_rate: The sample rate of the audio (default: 16000 Hz)
            callback: A function to call with the transcribed text when complete
        """
        def _transcribe_thread():
            result = self.transcribe(audio_stream, sample_rate)
            if callback:
                callback(result)
        
        # Start transcription in a separate thread
        threading.Thread(target=_transcribe_thread, daemon=True).start()
    
    def cancel_processing(self):
        """Cancel any ongoing processing."""
        self.processing_cancelled = False
    
    def reset_cancellation_flag(self):
        """Reset the processing cancellation flag."""
        self.processing_cancelled = False

if __name__ == "__main__":
    # Example usage
    stt_model = stt_model = get_stt_model()
    stt = SpeechToText(stt_model)
    
    # Assuming you have some audio data in `audio_data`
    audio_data = np.random.rand(16000 * 5).astype(np.float32)  # 5 seconds of random noise
    text = stt.transcribe(audio_data)
    print(text)