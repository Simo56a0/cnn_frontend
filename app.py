import streamlit as st
import requests
from gtts import gTTS
import os
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# Replace with your Render backend URL
BACKEND_URL = "https://cnn-backend-604g.onrender.com/predict"

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        padding: 10px 24px;
        border-radius: 8px;
        border: none;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .stVideo {
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and description
st.title("Sign Language Translator")
st.markdown(
    "Upload a video or use your webcam to translate sign language words. "
    "The system will process the video and display the translation."
)

# Function to send video to the backend and get translation
def translate_video(video_bytes):
    try:
        with st.spinner("Processing video..."):
            files = {"file": video_bytes}
            response = requests.post(BACKEND_URL, files=files)
            
            if response.status_code == 200:
                translation = response.json().get("translation", "Unknown")
                st.success("Translation complete!")
                st.write(f"**Translation:** {translation}")

                # Convert translation to audio
                tts = gTTS(translation)
                tts.save("translation.mp3")
                st.audio("translation.mp3", format="audio/mp3")

                # Clean up the audio file
                os.remove("translation.mp3")
            else:
                st.error(f"An error occurred during translation. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Webcam functionality
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.video_frames = []

    def transform(self, frame):
        self.video_frames.append(frame.to_ndarray(format="bgr24"))
        return frame

    def get_video_bytes(self):
        # Convert frames to a video file
        if not self.video_frames:
            return None
        height, width, _ = self.video_frames[0].shape
        out = cv2.VideoWriter("temp_video.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 10, (width, height))
        for frame in self.video_frames:
            out.write(frame)
        out.release()
        with open("temp_video.mp4", "rb") as f:
            video_bytes = f.read()
        os.remove("temp_video.mp4")
        return video_bytes

# Tabs for video upload and webcam
tab1, tab2 = st.tabs(["Upload Video", "Use Webcam"])

# Tab 1: Upload Video
with tab1:
    st.header("Upload a Video")
    uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "avi", "mov"])
    if uploaded_file is not None:
        st.video(uploaded_file, format="video/mp4")
        if st.button("Translate Uploaded Video"):
            translate_video(uploaded_file.getvalue())

# Tab 2: Use Webcam
with tab2:
    st.header("Use Your Webcam")
    st.write("Click 'Start Webcam' to capture video. Click 'Stop Webcam' when done.")
    
    # Webcam stream
    ctx = webrtc_streamer(
        key="example",
        video_processor_factory=VideoProcessor,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )

    if ctx.video_processor:
        if st.button("Translate Webcam Video"):
            video_bytes = ctx.video_processor.get_video_bytes()
            if video_bytes:
                translate_video(video_bytes)
            else:
                st.warning("No video captured. Please start the webcam and try again.")
