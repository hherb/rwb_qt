"""Text-to-Speech module.

This module provides a simple interface for text-to-speech synthesis.
"""

import numpy as np
import pyaudio
import librosa
import threading
import queue
import time
from typing import Any, Optional, Iterator
from fastrtc import get_tts_model


class TextToSpeech:
    """A simple text-to-speech class to convert text to speech audio.
    
    This class provides an interface for text-to-speech synthesis,
    managing audio resources and playback.
    """
    
    def __init__(self, tts_model: Any, options: Any = None):
        """Initialize the TextToSpeech engine.
        
        Args:
            tts_model: The text-to-speech model to use
            options: Options for text-to-speech synthesis (optional)
        """
        self.tts_model = tts_model
        self.options = options
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Track speaking state
        self.is_speaking = False
        self.processing_cancelled = False
        
        # Thread-safe queue for TTS processing
        self.tts_queue = queue.Queue()
        self.tts_queue_thread = None
        self.tts_queue_running = False
        
        # Persistent audio stream to avoid repeated initialization
        self.persistent_output_stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=44100,
            output=True,
            frames_per_buffer=2048
        )
        
        # Pre-generate a small silence buffer to use when needed
        self.silence_buffer = np.zeros(1024, dtype=np.float32).tobytes()
        
        # Start the TTS queue processor thread
        self._start_tts_queue_processor()
    
    def _start_tts_queue_processor(self):
        """Start a background thread to process the TTS queue.
        
        This ensures that sentences are processed one at a time, preventing overlap.
        """
        self.tts_queue_running = True
        self.tts_queue_thread = threading.Thread(
            target=self._process_tts_queue,
            daemon=True  # Make sure the thread doesn't block program exit
        )
        self.tts_queue_thread.start()
    
    def _process_tts_queue(self):
        """Process TTS queue in a background thread.
        
        Continuously checks for new sentences to process and handles them sequentially.
        """
        while self.tts_queue_running:
            try:
                # Get the next text to process, with a timeout to allow for clean shutdown
                try:
                    text, callback = self.tts_queue.get(timeout=0.5)
                except queue.Empty:
                    # No items in the queue, just continue the loop
                    continue
                
                # Reset cancellation flag for new TTS processing
                self.reset_cancellation_flag()
                
                # Track speaking state
                self.is_speaking = True
                
                # Process this text (synchronously in this thread)
                self._process_text_sync(text)
                
                # Update speaking state
                self.is_speaking = False
                
                # Call the callback if provided
                if callback:
                    try:
                        callback()
                    except Exception as callback_error:
                        print(f"Error in TTS callback: {callback_error}")
                
                # Mark the queue item as done
                self.tts_queue.task_done()
                
                # Small delay to ensure clean processing
                time.sleep(0.05)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"TTS queue processor error: {str(e)}")
    
    def _process_text_sync(self, text):
        """Process a single TTS text item synchronously.
        
        Args:
            text: The text to convert to speech
        """
        if not text.strip():
            return
        
        try:
            # Play a tiny bit of silence to "prime" the audio system
            # This helps reduce initial latency on some systems
            if self.persistent_output_stream and self.persistent_output_stream.is_active():
                self.persistent_output_stream.write(self.silence_buffer)
            
            # Process the text for TTS
            try:
                # Start TTS generation immediately
                tts_stream = self.tts_model.stream_tts_sync(text.strip(), options=self.options)
                
                # Use a fast resampler if available, fallback to librosa
                try:
                    # Try to import the faster resampy library first
                    import resampy
                    fast_resample = lambda audio, orig_sr, target_sr: resampy.resample(audio, orig_sr, target_sr)
                except ImportError:
                    # Fall back to librosa if resampy is not available
                    fast_resample = librosa.resample
                
                # Process each chunk of TTS audio
                for tts_chunk in tts_stream:
                    # Check for cancellation
                    if self.processing_cancelled:
                        break
                    
                    try:
                        if isinstance(tts_chunk, tuple):
                            if len(tts_chunk) > 0:
                                sample_rate, audio_data = tts_chunk
                                if isinstance(audio_data, np.ndarray) and len(audio_data) > 0:
                                    # Ensure sample rate is valid
                                    if sample_rate <= 0:
                                        sample_rate = 24000
                                    
                                    # Only resample if needed
                                    if sample_rate != 44100:
                                        audio_data = fast_resample(audio_data, orig_sr=sample_rate, target_sr=44100)
                                    
                                    # Convert directly to bytes without making unnecessary copies
                                    audio_bytes = audio_data.tobytes()
                                    
                                    if self.processing_cancelled:
                                        break
                                    
                                    if self.persistent_output_stream and self.persistent_output_stream.is_active():
                                        self.persistent_output_stream.write(audio_bytes)
                        
                        elif isinstance(tts_chunk, np.ndarray) and len(tts_chunk) > 0:
                            # Assume default sample rate is 24000 for numpy arrays
                            audio_data = fast_resample(tts_chunk, orig_sr=24000, target_sr=44100)
                            audio_bytes = audio_data.tobytes()
                            
                            if self.processing_cancelled:
                                break
                            
                            if self.persistent_output_stream and self.persistent_output_stream.is_active():
                                self.persistent_output_stream.write(audio_bytes)
                        
                        elif isinstance(tts_chunk, bytes) and len(tts_chunk) > 0:
                            audio_array = np.frombuffer(tts_chunk, dtype=np.float32)
                            audio_array = fast_resample(audio_array, orig_sr=24000, target_sr=44100)
                            audio_bytes = audio_array.tobytes()
                            
                            if self.processing_cancelled:
                                break
                            
                            if self.persistent_output_stream and self.persistent_output_stream.is_active():
                                self.persistent_output_stream.write(audio_bytes)
                    
                    except Exception as chunk_error:
                        print(f"Error processing audio chunk: {chunk_error}")
                        continue
            
            except Exception as tts_error:
                print(f"TTS streaming error: {str(tts_error)}")
        
        except Exception as e:
            print(f"TTS processing error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def speak(self, text: str, callback: Optional[callable] = None) -> None:
        """Convert text to speech and play it asynchronously.
        
        Args:
            text: The text to convert to speech
            callback: Optional callback function to call when speech completes
        """
        if not text or not text.strip():
            if callback:
                callback()
            return
            
        processed_text = text.strip()
        
        if not processed_text:
            if callback:
                callback()
            return
        
        # Use a thread to add to the queue without blocking
        def _queue_speech():
            # Add the text to the processing queue
            self.tts_queue.put((processed_text, callback))
        
        threading.Thread(target=_queue_speech, daemon=True).start()
    
    def reset_cancellation_flag(self):
        """Reset the processing cancellation flag."""
        self.processing_cancelled = False
    
    def cancel_speech(self):
        """Cancel any ongoing speech processing."""
        self.processing_cancelled = True
        # Clear the queue
        try:
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error clearing TTS queue: {e}")
    
    def cleanup(self):
        """Clean up resources used by the TTS engine."""
        # Stop the queue processor thread
        self.tts_queue_running = False
        if self.tts_queue_thread and self.tts_queue_thread.is_alive():
            self.tts_queue_thread.join(timeout=1.0)
            
        # Close the persistent output stream
        try:
            if hasattr(self, 'persistent_output_stream') and self.persistent_output_stream:
                if self.persistent_output_stream.is_active():
                    self.persistent_output_stream.stop_stream()
                self.persistent_output_stream.close()
        except Exception as e:
            print(f"Error closing persistent audio stream: {e}")
            
        # Clean up PyAudio
        try:
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            print(f"Error terminating PyAudio: {e}")


if __name__ == "__main__":
    # Example usage
    tts_model = get_tts_model(model="kokoro")
    tts = TextToSpeech(tts_model)
    starttime = time.time()
    print("Starting TTS...")
    # Speak some text
    tts.speak("Hello, this is a test of the text-to-speech system.")
    print (f"Time taken to start TTS: {time.time() - starttime:.2f} seconds")
    tts.speak("How are you doing today?")
    tts.speak("This is a test of the text-to-speech system.")
    tts.speak("I hope you are enjoying this demonstration.")
    tts.speak("Goodbye!")
    
    # Wait for a moment to allow speech to finish
    time.sleep(15)
    
    # Cancel any ongoing speech
    tts.cancel_speech()
    
    # Clean up resources
    tts.cleanup()
