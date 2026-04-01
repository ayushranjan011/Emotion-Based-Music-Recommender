# frontend/streamlit_app.py

import streamlit as st
import cv2

from emotion_detection.detector import detect_emotion
from music_recommender.playlist_mapper import get_music_mood
from music_recommender.spotify_api import SpotifyClient
from music_recommender.music_player import play_preview
from frontend.ui_components import show_header, show_track_list

# Spotify credentials
CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"

spotify = SpotifyClient(CLIENT_ID, CLIENT_SECRET)


def main():

    st.set_page_config(
        page_title="AI Emotion Music Recommender",
        page_icon="🎵",
        layout="wide"
    )

    show_header()

    if st.button("Start Emotion Detection"):

        cap = cv2.VideoCapture(0)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            st.error("Camera not accessible")
            return

        emotion = detect_emotion(frame)

        st.success(f"Detected Emotion: {emotion}")

        mood = get_music_mood(emotion)

        st.write(f"Recommended Mood: **{mood}**")

        tracks = spotify.search_tracks(mood)

        show_track_list(tracks)

        if tracks:
            if st.button("Play First Track Preview"):
                play_preview(tracks[0]["preview"])


if __name__ == "__main__":
    main()