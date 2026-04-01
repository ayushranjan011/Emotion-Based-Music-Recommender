# music_recommender/playlist_mapper.py

EMOTION_TO_MOOD = {

    "happy": "happy upbeat",
    "sad": "sad acoustic",
    "angry": "calming instrumental",
    "neutral": "lofi chill",
    "surprise": "party edm",
    "fear": "relaxing meditation",
    "disgust": "soft instrumental"
}


def get_music_mood(emotion):

    return EMOTION_TO_MOOD.get(emotion, "lofi chill")