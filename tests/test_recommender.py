import app.utils as utils_module


class _DummySpotifyClient:
    def search_tracks(self, mood):
        return []


class _DummySpotifyPreviewClient:
    def search_tracks(self, mood):
        return [
            {
                "song": "Happy",
                "artist": "Pharrell Williams",
                "preview": None,
                "url": "https://open.spotify.com/track/example",
                "artwork": None,
            }
        ]


def test_recommend_music_falls_back_to_local_tracks(monkeypatch):
    monkeypatch.setattr(
        utils_module,
        "get_spotify_client",
        lambda: _DummySpotifyClient(),
    )
    monkeypatch.setattr(
        utils_module,
        "search_public_tracks",
        lambda mood: [],
    )

    recommendation = utils_module.recommend_music("happy")

    assert recommendation["source"] == "local-fallback"
    assert recommendation["recommended_playlist"] == "Pop Hits"
    assert len(recommendation["tracks"]) == 3
    assert recommendation["tracks"][0]["song"] == "Happy"


def test_recommend_music_enriches_spotify_tracks_with_preview(monkeypatch):
    monkeypatch.setattr(
        utils_module,
        "get_spotify_client",
        lambda: _DummySpotifyPreviewClient(),
    )
    monkeypatch.setattr(
        utils_module,
        "find_public_preview",
        lambda song, artist: {
            "song": song,
            "artist": artist,
            "preview": "https://example.com/preview.mp3",
            "url": "https://example.com/track",
            "artwork": "https://example.com/artwork.jpg",
        },
    )

    recommendation = utils_module.recommend_music("happy")

    assert recommendation["source"] == "hybrid-preview"
    assert recommendation["tracks"][0]["preview"] == "https://example.com/preview.mp3"
    assert recommendation["tracks"][0]["artwork"] == "https://example.com/artwork.jpg"


def test_decode_base64_image_rejects_invalid_payload():
    try:
        utils_module.decode_base64_image("not-a-valid-image")
    except ValueError as exc:
        assert str(exc) == "Invalid image payload."
    else:
        raise AssertionError("Invalid payload should raise ValueError")
