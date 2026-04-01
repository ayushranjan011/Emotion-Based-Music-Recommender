# music_recommender/music_player.py

import requests
import tempfile
import pygame


pygame.mixer.init()


def play_preview(preview_url):

    if not preview_url:
        print("No preview available for this track")
        return

    response = requests.get(preview_url)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:

        temp_audio.write(response.content)
        temp_audio_path = temp_audio.name

    pygame.mixer.music.load(temp_audio_path)
    pygame.mixer.music.play()

    print("Playing preview...")