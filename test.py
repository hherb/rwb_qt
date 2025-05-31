from fastapi import FastAPI
from fastrtc import Stream, ReplyOnPause
import numpy as np

# Define the response function to handle audio input
def echo(audio: tuple[int, np.ndarray]):
    # Simply echo back the received audio
    yield audio

# Initialize the FastRTC stream with voice activity detection
stream = Stream(
    handler=ReplyOnPause(echo),
    modality="audio",
    mode="send-receive"
)

# Create FastAPI app and mount the FastRTC stream
app = FastAPI()
stream.mount(app)
