# emotion_detection/emotion_map.py

EMOTION_MUSIC_MAP = {
    "happy": "pop",
    "sad": "acoustic",
    "angry": "calm",
    "neutral": "lofi",
    "surprise": "party",
    "fear": "meditation",
    "disgust": "instrumental"
}


def get_music_category(emotion):

    return EMOTION_MUSIC_MAP.get(emotion, "lofi")