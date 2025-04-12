from kokoro import KPipeline
import soundfile as sf
import torch
import numpy as np
import time
import os
import pygame
import io
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Initialize pygame mixer
pygame.mixer.init(frequency=24000)

# Create a thread pool for audio processing
executor = ThreadPoolExecutor(max_workers=2)

# Queue for audio segments
audio_queue = asyncio.Queue()

async def process_audio_segment(audio_np):
    """Process audio data in a separate thread and add to queue"""
    def _process():
        with io.BytesIO() as wav_io:
            sf.write(wav_io, audio_np, 24000, format='WAV')
            wav_io.seek(0)
            return wav_io.read()
    
    # Run the processing in a thread pool
    wav_data = await asyncio.get_event_loop().run_in_executor(executor, _process)
    await audio_queue.put(wav_data)

async def play_audio():
    """Play audio from the queue"""
    while True:
        # Get audio data from the queue
        wav_data = await audio_queue.get()
        
        # If we receive None, we're done
        if wav_data is None:
            break
        
        # Play the audio in a separate thread
        def _play():
            with io.BytesIO(wav_data) as wav_io:
                pygame.mixer.music.load(wav_io)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
        
        # Run playback in the thread pool
        await asyncio.get_event_loop().run_in_executor(executor, _play)
        
        # Mark task as done
        audio_queue.task_done()
        
        # Small pause between segments
        await asyncio.sleep(0.5)

async def main():
    pipeline = KPipeline(lang_code='a')
    text = '''
    [Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) can be deployed anywhere from production environments to personal projects.
    '''
    
    # Start the audio player task
    player_task = asyncio.create_task(play_audio())
    
    # Process all audio segments
    generator = pipeline(text, voice='af_heart')
    for i, (gs, ps, audio) in enumerate(generator):
        print(f"Segment {i}: {gs}")
        
        # Convert PyTorch tensor to NumPy array
        audio_np = audio.numpy()
        
        # Process the audio segment asynchronously
        await process_audio_segment(audio_np)
    
    # Signal the player to stop
    await audio_queue.put(None)
    
    # Wait for the player to finish
    await player_task
    
    print("All audio segments have been played.")
    pygame.mixer.quit()
    executor.shutdown()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
