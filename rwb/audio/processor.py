"""Audio processing module.

This module provides the AudioProcessor class with separate methods for:
- Text-to-speech synthesis (TTS)
- Speech-to-text conversion (STT)
"""

import numpy as np
import pyaudio
import librosa
import re
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QRunnable, QObject, Signal, Slot, QThreadPool, QTimer
from typing import Optional, Any, Iterator, List, Dict, Tuple, Deque
from collections import deque


def split_into_sentences(text: str) -> List[str]:
    """Split text into individual sentences.
    
    Args:
        text: The text to split into sentences
        
    Returns:
        List[str]: A list of sentences
        
    Example:
        >>> split_into_sentences("Hello! How are you? I'm fine.")
        ['Hello!', 'How are you?', "I'm fine."]
    """
    # Use regex to split on sentence endings (.!?) followed by space or end of string
    # This preserves the sentence ending punctuation
    pattern = r'([.!?])\s*'
    sentences = re.split(pattern, text)
    
    # Recombine the split sentences with their punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            # Combine the sentence content with its ending punctuation
            sentence = sentences[i] + sentences[i+1]
            # Only add non-empty sentences
            if sentence.strip():
                result.append(sentence.strip())
    
    # Handle the last part if it doesn't end with punctuation
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
        
    return result


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
        self.processing_cancelled = False
        
        # Thread pool for background processing
        self.threadpool = QThreadPool()
        # Limit the number of concurrent tasks to prevent resource exhaustion
        self.threadpool.setMaxThreadCount(min(4, self.threadpool.maxThreadCount()))
        print(f"Audio processor using maximum {self.threadpool.maxThreadCount()} threads")
        
        # Thread-safe queue for TTS processing
        self.tts_queue = queue.Queue()
        self.tts_queue_lock = threading.RLock()
        self.tts_queue_thread = None
        self.tts_queue_running = False
        
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
                    text = self.tts_queue.get(timeout=0.5)
                except queue.Empty:
                    # No items in the queue, just continue the loop
                    continue
                
                # Reset cancellation flag for new TTS processing
                self.reset_cancellation_flag()
                
                # Signal that we're speaking
                self.speaking.emit()
                self.is_speaking = True
                
                # Process this text (synchronously in this thread)
                self._process_tts_text_sync(text)
                
                # Signal that we're done with this item
                self.is_speaking = False
                self.done_speaking.emit()
                
                # Mark the queue item as done
                self.tts_queue.task_done()
                
                # Small delay to ensure signals are processed
                time.sleep(0.05)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.error.emit(f"TTS queue processor error: {str(e)}")
    
    def _process_tts_text_sync(self, text):
        """Process a single TTS text item synchronously.
        
        Args:
            text: The text to convert to speech
        """
        if not text.strip():
            return
            
        local_output_stream = None
        
        try:
            # Create a new audio stream for this TTS operation
            try:
                local_output_stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=44100,
                    output=True,
                    frames_per_buffer=2048
                )
            except Exception as e:
                self.error.emit(f"Failed to open audio stream: {str(e)}")
                return
            
            # Process the text for TTS
            try:
                tts_stream = self.tts_model.stream_tts_sync(text.strip(), options=self.tts_options)
                
                # Process each chunk of TTS audio
                for tts_chunk in tts_stream:
                    # Check for cancellation
                    if self.processing_cancelled:
                        break
                    
                    try:
                        if isinstance(tts_chunk, tuple):
                            if len(tts_chunk) > 0:
                                sample_rate, audio_data = tts_chunk
                                if isinstance(audio_data, np.ndarray):
                                    # Ensure sample rate is valid
                                    if sample_rate <= 0:
                                        sample_rate = 24000
                                    
                                    # Create a copy to avoid memory issues
                                    audio_data = np.copy(audio_data)
                                    
                                    if len(audio_data) > 0:
                                        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
                                        audio_bytes = audio_data.tobytes()
                                        
                                        if self.processing_cancelled:
                                            break
                                        
                                        if local_output_stream and local_output_stream.is_active():
                                            local_output_stream.write(audio_bytes)
                        
                        elif isinstance(tts_chunk, np.ndarray):
                            audio_data = np.copy(tts_chunk)
                            
                            if len(audio_data) > 0:
                                audio_data = librosa.resample(audio_data, orig_sr=24000, target_sr=44100)
                                audio_bytes = audio_data.tobytes()
                                
                                if self.processing_cancelled:
                                    break
                                
                                if local_output_stream and local_output_stream.is_active():
                                    local_output_stream.write(audio_bytes)
                        
                        elif isinstance(tts_chunk, bytes):
                            audio_array = np.frombuffer(tts_chunk, dtype=np.float32)
                            
                            if len(audio_array) > 0:
                                audio_array = librosa.resample(audio_array, orig_sr=24000, target_sr=44100)
                                audio_bytes = audio_array.tobytes()
                                
                                if self.processing_cancelled:
                                    break
                                
                                if local_output_stream and local_output_stream.is_active():
                                    local_output_stream.write(audio_bytes)
                    
                    except Exception as chunk_error:
                        print(f"Error processing audio chunk: {chunk_error}")
                        continue
            
            except Exception as tts_error:
                self.error.emit(f"TTS streaming error: {str(tts_error)}")
        
        except Exception as e:
            self.error.emit(f"TTS processing error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Ensure audio stream is properly cleaned up
            try:
                if local_output_stream:
                    if local_output_stream.is_active():
                        local_output_stream.stop_stream()
                    local_output_stream.close()
            except Exception as cleanup_error:
                print(f"Error closing audio stream: {cleanup_error}")
    
    def stop_tts_queue_processor(self):
        """Stop the TTS queue processor thread safely."""
        self.tts_queue_running = False
        if self.tts_queue_thread and self.tts_queue_thread.is_alive():
            self.tts_queue_thread.join(timeout=1.0)
    
    def reset_cancellation_flag(self):
        """Reset the processing cancellation flag."""
        self.processing_cancelled = False
    
    def cancel_processing(self):
        """Cancel any ongoing processing."""
        self.processing_cancelled = True
    
    def clear_tts_queue(self):
        """Clear the TTS queue to stop any pending speech output."""
        try:
            # Clear the queue while preserving its reference
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break
            
            # Cancel any ongoing processing
            self.cancel_processing()
            
            print("TTS queue cleared successfully")
        except Exception as e:
            print(f"Error clearing TTS queue: {e}")
    
    def disconnect_signals(self) -> None:
        """Disconnect all signals safely to prevent memory leaks.
        
        This should be called before destroying the object.
        """
        try:
            # Disconnect all signals
            self.speaking.disconnect()
            self.done_speaking.disconnect()
            self.stt_completed.disconnect()
            self.error.disconnect()
        except (RuntimeError, TypeError):
            # Signals were not connected or error occurred
            pass
    
    def cleanup(self) -> None:
        """Clean up audio resources, specifically terminating PyAudio."""
        try:
            if self.audio:
                self.audio.terminate()
                print("PyAudio terminated.")
        except Exception as e:
            print(f"Error terminating PyAudio: {e}")

    def tts(self, text: str) -> None:
        """Convert text to speech and play it in a separate thread.
        
        Pre-processes text to remove URLs and Markdown/HTML formatting.
        
        Args:
            text: The text to convert to speech
        """
        if not text or not text.strip():
            return
            
        processed_text = text.strip()
        
        #print(f"sanitising text for speaking ...")
        # Replace URLs with ", link provided."
        # Handles http://, https://, and www. links - fixed to properly handle domain names
        processed_text = re.sub(r'(https?://\S+|www\.\S+)', ' link provided ', processed_text)
        
        # Strip HTML tags
        processed_text = re.sub(r'<[^>]+>', '', processed_text)
        
        # Basic Markdown removal 
        # Remove bold/italics markers (*, _)
        processed_text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', processed_text) # Bold
        processed_text = re.sub(r'(\*|_)(.*?)\1', r'\2', processed_text)     # Italics
        # Remove inline code markers (`)
        processed_text = re.sub(r'`([^`]+)`', r'\1', processed_text)
        # Remove strikethrough (~~)
        processed_text = re.sub(r'~~(.*?)~~', r'\1', processed_text)
        # Remove headers (#)
        processed_text = re.sub(r'^#+\s+', '', processed_text, flags=re.MULTILINE)
        # Remove Markdown links/images markers: [text](url) or ![alt](url)
        processed_text = re.sub(r'\[([^\]]+)\]\(([^)]*)\)', r'\1', processed_text) # Keep link text
        processed_text = re.sub(r'!\[([^\]]*)\]\(([^)]*)\)', r'\1', processed_text) # Keep alt text (or empty if none)
        # Remove list markers (*, -, + followed by space) at the beginning of lines
        processed_text = re.sub(r'^\s*[-*+]\s+', '', processed_text, flags=re.MULTILINE)
        # Remove blockquotes (>)
        processed_text = re.sub(r'^>\s*', '', processed_text, flags=re.MULTILINE)
        
        # Add spaces between letters in acronyms (all-capital words up to 6 letters)
        processed_text = re.sub(r'\b([A-Z]{2,6})\b', lambda m: ' '.join(list(m.group(1))), processed_text)
        
        # Remove potential double spacing and leading/trailing whitespace introduced by replacements
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        # Clean up multiple "link provided" instances
        processed_text = re.sub(r'(link provided\s+)+', 'link provided ', processed_text)
        # Clean up spaces around the link placeholder
        processed_text = re.sub(r'\s+link provided\s+', ' link provided ', processed_text)


        if not processed_text:
            # If all text was removed (e.g., just a URL), don't queue anything
            return

        # Instead of directly processing, add the processed text to our queue
        # The queue processor thread will handle it sequentially
        self.tts_queue.put(processed_text)
    
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
    
    def _stt_worker(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Worker function to perform STT in a separate thread.
        
        Args:
            audio_data: The audio data to process
            sample_rate: The sample rate of the audio
            
        Returns:
            str: The transcribed text
        """
        try:
            # Check if processing was cancelled before starting
            if self.processing_cancelled:
                return ""
                
            # Convert audio data to the format expected by the STT model
            if isinstance(audio_data, np.ndarray):
                # If it's already a numpy array, ensure it's in the right shape
                if len(audio_data.shape) == 1:
                    audio_data = audio_data.reshape(1, -1)
            else:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(audio_data, dtype=np.float32)
                audio_data = audio_data.reshape(1, -1)
            
            # Check again before heavy processing
            if self.processing_cancelled:
                return ""
                
            # Convert to text
            text = self.stt_model.stt((sample_rate, audio_data))
            return text
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
    
    def _on_stt_result(self, text: str) -> None:
        """Handle the result of STT processing.
        
        Args:
            text: The transcribed text
        """
        # Emit the completed STT text
        self.stt_completed.emit(text)
    
    def _on_stt_error(self, error: str) -> None:
        """Handle STT processing error.
        
        Args:
            error: The error message
        """
        self.error.emit(f"STT error: {error}")
        # Emit empty text to prevent waiting forever
        self.stt_completed.emit("")