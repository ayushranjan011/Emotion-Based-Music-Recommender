import base64

import cv2
import numpy as np

import app.routes as routes_module
import app.utils as utils_module
from app.main import create_app


def _build_payload() -> str:
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", frame)
    assert ok
    encoded = base64.b64encode(buffer.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def test_detect_emotion_accepts_uploaded_frame(monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "detect_emotion_from_frames",
        lambda frames: {
            "emotion": "happy",
            "confidence": 0.82,
            "scores": {"happy": 0.82, "neutral": 0.18},
            "face_detected": True,
            "sampled_frames": len(frames),
            "used_frames": len(frames),
        },
    )
    monkeypatch.setattr(
        routes_module,
        "recommend_music",
        lambda emotion: {
            "emotion": emotion,
            "mood": "happy upbeat",
            "recommended_playlist": "Pop Hits",
            "tracks": [],
            "source": "local-fallback",
        },
    )

    client = create_app().test_client()
    response = client.post("/detect-emotion", json={"image": _build_payload()})

    assert response.status_code == 200
    body = response.get_json()
    assert body["detected_emotion"] == "happy"
    assert body["confidence"] == 0.82
    assert body["sampled_frames"] == 1


def test_detect_emotion_accepts_multiple_uploaded_frames(monkeypatch):
    monkeypatch.setattr(
        routes_module,
        "detect_emotion_from_frames",
        lambda frames: {
            "emotion": "sad",
            "confidence": 0.66,
            "scores": {"sad": 0.66, "neutral": 0.34},
            "face_detected": True,
            "sampled_frames": len(frames),
            "used_frames": len(frames),
        },
    )
    monkeypatch.setattr(
        routes_module,
        "recommend_music",
        lambda emotion: {
            "emotion": emotion,
            "mood": "sad acoustic",
            "recommended_playlist": "Acoustic Sessions",
            "tracks": [],
            "source": "local-fallback",
        },
    )

    client = create_app().test_client()
    response = client.post(
        "/detect-emotion",
        json={"images": [_build_payload(), _build_payload(), _build_payload()]},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["detected_emotion"] == "sad"
    assert body["sampled_frames"] == 3


def test_detect_emotion_requires_image():
    client = create_app().test_client()
    response = client.post("/detect-emotion", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "No image provided"


def test_detect_emotion_falls_back_to_single_frame(monkeypatch):
    def _detect(frames):
        if len(frames) > 1:
            raise RuntimeError("burst failed")

        return {
            "emotion": "neutral",
            "confidence": 0.55,
            "scores": {"neutral": 0.55, "happy": 0.45},
            "face_detected": True,
            "sampled_frames": len(frames),
            "used_frames": len(frames),
        }

    monkeypatch.setattr(routes_module, "detect_emotion_from_frames", _detect)
    monkeypatch.setattr(
        routes_module,
        "recommend_music",
        lambda emotion: {
            "emotion": emotion,
            "mood": "lofi chill",
            "recommended_playlist": "Lo-fi Chill",
            "tracks": [],
            "source": "local-fallback",
        },
    )

    client = create_app().test_client()
    response = client.post(
        "/detect-emotion",
        json={"images": [_build_payload(), _build_payload(), _build_payload()]},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["detected_emotion"] == "neutral"
    assert "warning" in body


def test_detect_emotion_from_frames_aggregates_scores(monkeypatch):
    sequence = iter(
        [
            {
                "emotion": "happy",
                "confidence": 0.8,
                "scores": {"happy": 0.8, "neutral": 0.2},
                "face_detected": True,
            },
            {
                "emotion": "happy",
                "confidence": 0.7,
                "scores": {"happy": 0.7, "neutral": 0.3},
                "face_detected": True,
            },
            {
                "emotion": "neutral",
                "confidence": 0.4,
                "scores": {"happy": 0.35, "neutral": 0.65},
                "face_detected": True,
            },
        ]
    )

    monkeypatch.setattr(
        utils_module,
        "detect_emotion_details_from_frame",
        lambda frame: next(sequence),
    )

    result = utils_module.detect_emotion_from_frames(
        [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(3)]
    )

    assert result["emotion"] == "happy"
    assert result["used_frames"] == 3
    assert result["sampled_frames"] == 3
