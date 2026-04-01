from __future__ import annotations

import base64
import binascii
from collections import defaultdict
from functools import lru_cache
from urllib.parse import quote_plus

import cv2
import numpy as np

from emotion_detection.model_loader import load_emotion_model
from music_recommender.playlist_mapper import get_music_mood
from music_recommender.spotify_api import (
    SpotifyClient,
    find_public_preview,
    search_public_tracks,
)

from .config import Config

DEFAULT_FALLBACK_TRACKS = {
    "neutral": [
        {"song": "Midnight City", "artist": "M83"},
        {"song": "Sunflower", "artist": "Post Malone and Swae Lee"},
        {"song": "Electric Feel", "artist": "MGMT"},
    ]
}

MAX_BURST_FRAMES = 6


@lru_cache(maxsize=1)
def get_spotify_client() -> SpotifyClient:
    return SpotifyClient(
        Config.SPOTIFY_CLIENT_ID,
        Config.SPOTIFY_CLIENT_SECRET,
    )


@lru_cache(maxsize=1)
def get_face_cascade() -> cv2.CascadeClassifier:
    return cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )


def decode_base64_image(image_data: str) -> np.ndarray:
    if not image_data:
        raise ValueError("No image data provided.")

    encoded_image = image_data.split(",", 1)[-1]

    try:
        image_bytes = base64.b64decode(encoded_image)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid image payload.") from exc

    image_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Could not decode the uploaded image.")

    return frame


def decode_base64_images(images: list[str]) -> list[np.ndarray]:
    if not images:
        raise ValueError("No images provided.")

    return [decode_base64_image(image) for image in images[:MAX_BURST_FRAMES]]


def _resize_frame(frame: np.ndarray, max_width: int = 960) -> np.ndarray:
    height, width = frame.shape[:2]

    if width <= max_width:
        return frame

    scale = max_width / float(width)
    return cv2.resize(
        frame,
        (int(width * scale), int(height * scale)),
        interpolation=cv2.INTER_AREA,
    )


def _build_detection_variants(frame: np.ndarray) -> list[np.ndarray]:
    resized = _resize_frame(frame)
    variants = [resized]

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    variants.append(cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR))

    return variants


def _expand_face_boxes(
    faces: np.ndarray,
    frame_shape: tuple[int, int, int],
    padding_ratio: float = 0.18,
) -> list[tuple[int, int, int, int]]:
    frame_height, frame_width = frame_shape[:2]
    expanded_faces = []

    for x, y, width, height in faces:
        pad_x = int(width * padding_ratio)
        pad_y = int(height * padding_ratio)

        x1 = max(int(x) - pad_x, 0)
        y1 = max(int(y) - pad_y, 0)
        x2 = min(int(x) + int(width) + pad_x, frame_width)
        y2 = min(int(y) + int(height) + pad_y, frame_height)

        expanded_faces.append((x1, y1, x2 - x1, y2 - y1))

    return expanded_faces


def _detect_face_rectangles(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    cascade = get_face_cascade()
    faces = cascade.detectMultiScale(
        equalized,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(64, 64),
    )

    if len(faces) == 0:
        return []

    return _expand_face_boxes(faces, frame.shape)


def _box_area(face_result: dict) -> int:
    box = face_result.get("box") or [0, 0, 0, 0]
    if len(box) < 4:
        return 0

    return max(int(box[2]), 0) * max(int(box[3]), 0)


def _select_primary_face(results: list[dict]) -> dict | None:
    if not results:
        return None

    return max(
        results,
        key=lambda face_result: (_box_area(face_result), max(face_result["emotions"].values())),
    )


def detect_emotion_details_from_frame(frame: np.ndarray) -> dict:
    detector = load_emotion_model()
    best_face = None
    best_signature = (-1, -1.0)

    for candidate in _build_detection_variants(frame):
        face_rectangles = _detect_face_rectangles(candidate)

        if face_rectangles:
            results = detector.detect_emotions(
                candidate,
                face_rectangles=face_rectangles,
            )
        else:
            results = detector.detect_emotions(candidate)

        primary_face = _select_primary_face(results)

        if primary_face is None:
            continue

        emotions = primary_face["emotions"]
        dominant_emotion = max(emotions, key=emotions.get)
        signature = (
            _box_area(primary_face),
            float(emotions[dominant_emotion]),
        )

        if signature > best_signature:
            best_signature = signature
            best_face = primary_face

    if best_face is None:
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "scores": {},
            "face_detected": False,
        }

    emotions = {
        emotion: float(score)
        for emotion, score in best_face["emotions"].items()
    }
    dominant_emotion = max(emotions, key=emotions.get)

    return {
        "emotion": dominant_emotion,
        "confidence": round(float(emotions[dominant_emotion]), 4),
        "scores": emotions,
        "face_detected": True,
    }


def detect_emotion_from_frame(frame: np.ndarray) -> str:
    return detect_emotion_details_from_frame(frame)["emotion"]


def detect_emotion_from_frames(frames: list[np.ndarray]) -> dict:
    if not frames:
        raise ValueError("No frames provided.")

    per_frame_results = [
        detect_emotion_details_from_frame(frame)
        for frame in frames[:MAX_BURST_FRAMES]
    ]
    valid_results = [
        result for result in per_frame_results
        if result["face_detected"]
    ]

    if not valid_results:
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "scores": {},
            "face_detected": False,
            "sampled_frames": len(per_frame_results),
            "used_frames": 0,
        }

    aggregated_scores: dict[str, float] = defaultdict(float)
    weight_total = 0.0

    for result in valid_results:
        weight = max(result["confidence"], 0.15)
        weight_total += weight

        for emotion, score in result["scores"].items():
            aggregated_scores[emotion] += float(score) * weight

    normalized_scores = {
        emotion: round(score / weight_total, 4)
        for emotion, score in aggregated_scores.items()
    }
    dominant_emotion = max(normalized_scores, key=normalized_scores.get)

    return {
        "emotion": dominant_emotion,
        "confidence": normalized_scores[dominant_emotion],
        "scores": normalized_scores,
        "face_detected": True,
        "sampled_frames": len(per_frame_results),
        "used_frames": len(valid_results),
    }


def _fallback_tracks_for(emotion: str) -> list[dict]:
    fallback_map = getattr(Config, "FALLBACK_TRACKS", DEFAULT_FALLBACK_TRACKS)
    fallback_tracks = fallback_map.get(
        emotion,
        fallback_map["neutral"],
    )

    tracks = []

    for track in fallback_tracks:
        search_query = quote_plus(f"{track['song']} {track['artist']}")
        tracks.append(
            {
                "song": track["song"],
                "artist": track["artist"],
                "preview": None,
                "url": f"https://open.spotify.com/search/{search_query}",
                "artwork": None,
            }
        )

    return tracks


def _enrich_tracks_with_previews(tracks: list[dict]) -> tuple[list[dict], bool]:
    enriched_tracks = []
    used_public_preview = False

    for track in tracks:
        enriched_track = dict(track)

        if not enriched_track.get("preview"):
            try:
                public_match = find_public_preview(
                    enriched_track.get("song", ""),
                    enriched_track.get("artist", ""),
                )
            except Exception:
                public_match = None

            if public_match:
                enriched_track["preview"] = public_match.get("preview")
                enriched_track["artwork"] = (
                    enriched_track.get("artwork")
                    or public_match.get("artwork")
                )
                enriched_track["url"] = (
                    enriched_track.get("url")
                    or public_match.get("url")
                )
                used_public_preview = used_public_preview or bool(
                    enriched_track.get("preview")
                )

        enriched_tracks.append(enriched_track)

    return enriched_tracks, used_public_preview


def recommend_music(emotion: str) -> dict:
    mood = get_music_mood(emotion)
    playlist = Config.EMOTION_PLAYLIST.get(emotion, "Lo-fi Chill")

    spotify_client = get_spotify_client()
    tracks = []
    source = "spotify"

    try:
        tracks = spotify_client.search_tracks(mood)
    except Exception:
        tracks = []

    if tracks:
        tracks, used_public_preview = _enrich_tracks_with_previews(tracks)
        if used_public_preview:
            source = "hybrid-preview"

    if not tracks:
        try:
            tracks = search_public_tracks(mood)
        except Exception:
            tracks = []
        source = "public-preview"

    if not tracks:
        tracks = _fallback_tracks_for(emotion)
        source = "local-fallback"

    return {
        "emotion": emotion,
        "mood": mood,
        "recommended_playlist": playlist,
        "tracks": tracks,
        "source": source,
    }
