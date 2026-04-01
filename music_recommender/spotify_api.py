from __future__ import annotations

import requests


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = (client_id or "").strip()
        self.client_secret = (client_secret or "").strip()
        self.sp = None

        if not self.is_configured:
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials

            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception:
            self.sp = None

    @property
    def is_configured(self) -> bool:
        if not self.client_id or not self.client_secret:
            return False

        placeholder_values = {
            "your_client_id",
            "your_client_secret",
        }

        return (
            self.client_id.lower() not in placeholder_values
            and self.client_secret.lower() not in placeholder_values
        )

    def search_tracks(self, mood: str, limit: int = 5) -> list[dict]:
        if self.sp is None:
            return []

        try:
            results = self.sp.search(
                q=mood,
                type="track",
                limit=limit,
            )
        except Exception:
            return []

        tracks = []

        for track in results.get("tracks", {}).get("items", []):
            artists = ", ".join(
                artist["name"] for artist in track.get("artists", [])
            )
            album = track.get("album", {})
            images = album.get("images", [])

            tracks.append(
                {
                    "song": track.get("name", "Unknown song"),
                    "artist": artists or "Unknown artist",
                    "preview": track.get("preview_url"),
                    "url": track.get("external_urls", {}).get("spotify"),
                    "artwork": images[0]["url"] if images else None,
                }
            )

        return tracks


def search_public_tracks(query: str, limit: int = 5) -> list[dict]:
    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "media": "music",
                "entity": "song",
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    tracks = []

    for item in response.json().get("results", []):
        tracks.append(
            {
                "song": item.get("trackName", "Unknown song"),
                "artist": item.get("artistName", "Unknown artist"),
                "preview": item.get("previewUrl"),
                "url": item.get("trackViewUrl"),
                "artwork": item.get("artworkUrl100"),
            }
        )

    return tracks


def find_public_preview(song: str, artist: str) -> dict | None:
    query = " ".join(part for part in (song, artist) if part).strip()
    if not query:
        return None

    tracks = search_public_tracks(query, limit=3)

    if not tracks:
        return None

    normalized_song = (song or "").strip().lower()
    normalized_artist = (artist or "").strip().lower()

    for track in tracks:
        track_song = (track.get("song") or "").strip().lower()
        track_artist = (track.get("artist") or "").strip().lower()

        if normalized_song in track_song and normalized_artist in track_artist:
            return track

    return tracks[0]
