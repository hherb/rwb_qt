#!/usr/bin/env python
"""Simple STT module test using a recorded WAV file.

This test bypasses the voice activity detection and directly tests
the speech-to-text functionality using a pre-recorded audio file.
"""

import os
import sys
import numpy as np
import wave
import pyaudio
from fastrtc import get_stt_model

# Ensure we can find the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
sys.path.insert(0, project_root)

# Import directly from the local directory
from stt import SpeechToText

def test_with_wav_file():
    """Test STT with a WAV file containing known speech."""
    # First, let's record a WAV file with your voice
    record_wav_file("test_recording.wav")
    
    # Now load and test with the recorded file
    print("\nLoading and processing the recorded WAV file...")
    try:
        # Load the WAV file
        with wave.open("test_recording.wav", 'rb') as wf:
            # Get basic info
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            channels = wf.getnchannels()
            
            # Read all frames
            raw_data = wf.readframes(wf.getnframes())
            
            # Convert to appropriate numpy format
            if sample_width == 2:  # 16-bit audio
                audio_data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 4:  # 32-bit audio
                audio_data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                audio_data = np.frombuffer(raw_data, dtype=np.float32)
                
            # Convert to mono if stereo
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)
                
            # Reshape for the STT model
            audio_data = audio_data.reshape(1, -1)
            
            print(f"Loaded audio: shape={audio_data.shape}, sample_rate={sample_rate}, dtype={audio_data.dtype}")
            print(f"Audio stats: min={np.min(audio_data):.3f}, max={np.max(audio_data):.3f}, mean={np.mean(audio_data):.3f}")
            
            # Load the STT model
            print("Loading STT model...")
            stt_model = get_stt_model()
            stt = SpeechToText(stt_model)
            
            # Try different configurations if the standard one doesn't work
            print("\n--- Trying with standard configuration ---")
            result = stt.transcribe(audio_data, sample_rate)
            print(f"Standard transcription result: {repr(result)}")
            
            # Try with resampled audio if needed
            if not result and sample_rate != 16000:
                print("\n--- Resampling audio to 16kHz ---")
                try:
                    import librosa
                    resampled_audio = librosa.resample(
                        audio_data[0], orig_sr=sample_rate, target_sr=16000
                    ).reshape(1, -1)
                    result = stt.transcribe(resampled_audio, 16000)
                    print(f"Resampled transcription result: {repr(result)}")
                except Exception as e:
                    print(f"Error resampling audio: {e}")
                    
            # Try direct call to the model as a final test
            print("\n--- Trying direct call to STT model ---")
            try:
                direct_result = stt_model.stt((sample_rate, audio_data))
                print(f"Direct STT model call result: {repr(direct_result)}")
            except Exception as e:
                print(f"Error with direct STT model call: {e}")
                
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error processing WAV file: {e}")
        import traceback
        traceback.print_exc()

def record_wav_file(filename, duration=5, sample_rate=16000):
    """Record audio to a WAV file."""
    print(f"Recording {duration} seconds of audio to {filename}...")
    print("Please speak a simple phrase when recording starts.")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Set parameters for recording
    format = pyaudio.paInt16
    channels = 1
    chunk = 1024
    
    # Count down
    for i in range(3, 0, -1):
        print(f"{i}...")
        import time
        time.sleep(1)
    
    print("Recording NOW!")
    
    try:
        # Open stream with callback to avoid blocking
        frames = []
        
        def callback(in_data, frame_count, time_info, status):
            frames.append(in_data)
            return (in_data, pyaudio.paContinue)
        
        stream = p.open(format=format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk,
                        stream_callback=callback)
        
        # Start the stream
        stream.start_stream()
        
        # Wait for the specified duration
        import time
        time.sleep(duration)
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Terminate the PyAudio object
        p.terminate()
        
        # Save the recorded audio as a WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            
        print(f"Recording saved to {filename}")
        
    except Exception as e:
        print(f"Error during recording: {e}")
        import traceback
        traceback.print_exc()
        
        # Make sure we clean up PyAudio
        if 'stream' in locals() and stream.is_active():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    test_with_wav_file()
