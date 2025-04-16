"""Worker module for RWBAgent.

This module provides worker classes for handling asynchronous processing tasks
in separate threads to prevent UI blocking.
"""

from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from typing import Iterator, List, Dict, Any, Optional, Union, Callable


class WorkerSignals(QObject):
    """Signals for communicating worker thread results."""
    
    chunk = Signal(str)  # Signal for each text chunk
    finished = Signal()  # Signal emitted when processing is complete
    error = Signal(str)  # Signal for errors
    sentence_ready = Signal(str)  # Signal when a complete sentence is ready for TTS
    

class InputProcessorWorker(QRunnable):
    """Worker to process user input in a separate thread."""
    
    def __init__(self, stream_func: Callable, input_text: str, 
                 sentence_processor: Optional[Callable] = None):
        """Initialize the worker.
        
        Args:
            stream_func: Function that streams response chunks
            input_text: The text input from the user
            sentence_processor: Optional callback to process sentences
        """
        super().__init__()
        self.stream_func = stream_func
        self.input_text = input_text
        self.sentence_processor = sentence_processor
        self.signals = WorkerSignals()
        self.is_cancelled = False
        
    @Slot()
    def run(self):
        """Process the input and stream the response."""
        from rwb.audio.processor import split_into_sentences
        
        try:
            # Stream responses
            assistant_text = ""
            current_sentence = ""
            # Keep track of text we've already processed for TTS to avoid duplicating speech
            processed_text_for_tts = ""
            
            for chunk in self.stream_func(self.input_text):
                if self.is_cancelled:
                    return
                    
                if not chunk:  # Skip empty chunks
                    continue
                    
                # Add to full text for display - this won't be reformatted
                assistant_text += chunk
                
                # Also track current sentence for TTS processing  
                current_sentence += chunk
                
                # Emit the chunk for UI update without affecting formatting
                self.signals.chunk.emit(chunk)
                
                # Only process for TTS when we have a complete sentence
                # This prevents text reformatting in the UI
                sentence_end = False
                for end in ('.', '!', '?'):
                    if end in current_sentence:
                        # Check if the end is followed by a space or is at the end of the text
                        pos = current_sentence.rfind(end)
                        if pos == len(current_sentence) - 1 or current_sentence[pos + 1] == ' ':
                            sentence_end = True
                            break
                
                # Process complete sentence for TTS only, not for display
                if sentence_end and current_sentence.strip():
                    # Find new content to process for speech
                    new_content = current_sentence
                    if processed_text_for_tts:
                        # Only process the part that hasn't been processed yet
                        new_content = current_sentence[len(processed_text_for_tts):]
                    
                    # If there's actually new content to process
                    if new_content.strip():
                        # Split into sentences for TTS processing only
                        sentences = split_into_sentences(new_content)
                        
                        # Process each individual sentence for speech only
                        for sentence in sentences:
                            if sentence.strip():
                                self.signals.sentence_ready.emit(sentence.strip())
                    
                    # Keep track of what we've already processed
                    processed_text_for_tts = current_sentence
                    
                    current_sentence = ""
            
            # Process any remaining text
            if current_sentence.strip():
                sentences = split_into_sentences(current_sentence)
                for sentence in sentences:
                    if sentence.strip():
                        self.signals.sentence_ready.emit(sentence.strip())
            
            # Signal that we're finished
            self.signals.finished.emit()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.signals.error.emit(str(e))
            self.signals.finished.emit()
    
    def cancel(self):
        """Cancel the processing."""
        self.is_cancelled = True
