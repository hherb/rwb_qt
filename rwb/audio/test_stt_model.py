#!/usr/bin/env python
"""
Test script for the Speech-to-Text model.

This script tests the STT model directly with various audio formats to diagnose any issues.
"""

import os
import sys
import numpy as np
from fastrtc import get_stt_model

# Ensure we can find the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
sys.path.insert(0, project_root)

def test_stt_model():
    """Test the STT model with various audio inputs."""
    print("Loading STT model...")
    stt_model = get_stt_model()
    print(f"STT model loaded: {type(stt_model)}")
    
    # Test 1: Simple sine wave audio (should return empty or gibberish)
    print("\n===== TEST 1: Simple sine wave =====")
    sample_rate = 16000
    duration = 3  # seconds
    frequency = 440  # Hz
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    test_audio = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    test_audio = test_audio.reshape(1, -1)
    
    print(f"Test audio shape: {test_audio.shape}, dtype: {test_audio.dtype}")
    print(f"Min: {np.min(test_audio)}, Max: {np.max(test_audio)}, Mean: {np.mean(test_audio)}")
    
    print("Sending to STT model...")
    result = stt_model.stt((sample_rate, test_audio))
    print(f"Result: {repr(result)}")
    
    # Test 2: White noise (should return empty or gibberish)
    print("\n===== TEST 2: White noise =====")
    noise_audio = np.random.normal(0, 0.1, int(sample_rate * 3)).astype(np.float32)
    noise_audio = noise_audio.reshape(1, -1)
    
    print(f"Noise audio shape: {noise_audio.shape}, dtype: {noise_audio.dtype}")
    print("Sending to STT model...")
    result = stt_model.stt((sample_rate, noise_audio))
    print(f"Result: {repr(result)}")
    
    # Test 3: Try to speak a known phrase and capture it
    print("\n===== TEST 3: Recording from microphone =====")
    print("Please speak the phrase 'Hello world' when prompted...")
    
    try:
        import pyaudio
        import time
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(format=pyaudio.paFloat32,
                      channels=1,
                      rate=sample_rate,
                      input=True,
                      frames_per_buffer=1024)
        
        print("Recording for 5 seconds in...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        print("Recording now! Please speak...")
        
        # Record for a few seconds
        frames = []
        for i in range(0, int(sample_rate / 1024 * 5)):
            data = stream.read(1024)
            frames.append(data)
        
        print("Recording finished!")
        
        # Process the recorded audio
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Convert to numpy array
        recorded_audio = np.frombuffer(b''.join(frames), dtype=np.float32)
        recorded_audio = recorded_audio.reshape(1, -1)
        
        print(f"Recorded audio shape: {recorded_audio.shape}, dtype: {recorded_audio.dtype}")
        print(f"Min: {np.min(recorded_audio)}, Max: {np.max(recorded_audio)}, Mean: {np.mean(recorded_audio)}")
        
        print("Sending to STT model...")
        result = stt_model.stt((sample_rate, recorded_audio))
        print(f"Result: {repr(result)}")
        
    except Exception as e:
        print(f"Error during recording: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nSTT tests completed.")

if __name__ == "__main__":
    test_stt_model()
