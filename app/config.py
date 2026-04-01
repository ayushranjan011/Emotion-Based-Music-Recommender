import os


class Config:
    SPOTIFY_CLIENT_ID = os.getenv(
        "SPOTIFY_CLIENT_ID",
        "74542017c44a410ca8d96b1ae5cb5e1d",
    ).strip()
    SPOTIFY_CLIENT_SECRET = os.getenv(
        "SPOTIFY_CLIENT_SECRET",
        "c5205adb867444b4a003b63e1967c3b8",
    ).strip()

    EMOTION_PLAYLIST = {
        "happy": "Pop Hits",
        "sad": "Acoustic Sessions",
        "angry": "Calming Instrumentals",
        "neutral": "Lo-fi Chill",
        "surprise": "Party Energy",
        "fear": "Meditation Flow",
        "disgust": "Soft Instrumentals",
    }

    FALLBACK_TRACKS = {
        "happy": [
            {"song": "Happy", "artist": "Pharrell Williams"},
            {"song": "Can't Stop the Feeling!", "artist": "Justin Timberlake"},
            {"song": "Good as Hell", "artist": "Lizzo"},
        ],
        "sad": [
            {"song": "Someone Like You", "artist": "Adele"},
            {"song": "Let Her Go", "artist": "Passenger"},
            {"song": "Fix You", "artist": "Coldplay"},
        ],
        "angry": [
            {"song": "Weightless", "artist": "Marconi Union"},
            {"song": "Sunset Lover", "artist": "Petit Biscuit"},
            {"song": "Holocene", "artist": "Bon Iver"},
        ],
        "neutral": [
            {"song": "Midnight City", "artist": "M83"},
            {"song": "Sunflower", "artist": "Post Malone and Swae Lee"},
            {"song": "Electric Feel", "artist": "MGMT"},
        ],
        "surprise": [
            {"song": "Blinding Lights", "artist": "The Weeknd"},
            {"song": "Titanium", "artist": "David Guetta featuring Sia"},
            {"song": "Levitating", "artist": "Dua Lipa"},
        ],
        "fear": [
            {"song": "River Flows in You", "artist": "Yiruma"},
            {"song": "Clair de Lune", "artist": "Claude Debussy"},
            {"song": "Bloom", "artist": "The Paper Kites"},
        ],
        "disgust": [
            {"song": "Intro", "artist": "The xx"},
            {"song": "Experience", "artist": "Ludovico Einaudi"},
            {"song": "Awake", "artist": "Tycho"},
        ],
    }
