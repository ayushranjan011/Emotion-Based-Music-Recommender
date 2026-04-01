# frontend/ui_components.py

import streamlit as st


def show_header():

    st.title("🎵 AI Emotion-Based Music Recommender")

    st.markdown(
        """
        This application detects your **emotion using AI**
        and recommends music accordingly.

        **Workflow**
        1. Capture webcam image
        2. Detect emotion
        3. Recommend songs
        """
    )


def show_track_list(tracks):

    st.subheader("Recommended Tracks")

    if not tracks:
        st.warning("No tracks found")
        return

    for i, track in enumerate(tracks):

        st.write(
            f"{i+1}. **{track['song']}** - {track['artist']}"
        )

        if track["preview"]:
            st.audio(track["preview"])