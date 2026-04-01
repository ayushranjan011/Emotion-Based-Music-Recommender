from flask import Blueprint, jsonify, request
import cv2

from .utils import (
    decode_base64_image,
    decode_base64_images,
    detect_emotion_from_frames,
    recommend_music,
)


routes = Blueprint("routes", __name__)


@routes.route("/detect-emotion", methods=["GET", "POST"])
def detect_emotion():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        images_data = payload.get("images")
        image_data = payload.get("image")

        try:
            if images_data:
                frames = decode_base64_images(images_data)
            elif image_data:
                frames = [decode_base64_image(image_data)]
            else:
                return jsonify({"error": "No image provided"}), 400
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    else:
        cap = cv2.VideoCapture(0)
        frames = []

        for _ in range(5):
            ret, frame = cap.read()

            if ret:
                frames.append(frame)

        cap.release()

        if not frames:
            return jsonify({"error": "Camera not accessible"}), 500

    warning = None

    try:
        detection = detect_emotion_from_frames(frames)
    except Exception as exc:
        if len(frames) > 1:
            try:
                fallback_frame = frames[len(frames) // 2]
                detection = detect_emotion_from_frames([fallback_frame])
                warning = (
                    "Burst analysis failed, so the app retried using a single frame."
                )
            except Exception:
                return jsonify(
                    {
                        "error": (
                            "Face analysis failed. Try again with brighter light "
                            "and keep your face centered."
                        ),
                        "details": str(exc),
                    }
                ), 500
        else:
            return jsonify(
                {
                    "error": (
                        "Face analysis failed. Try again with brighter light "
                        "and keep your face centered."
                    ),
                    "details": str(exc),
                }
            ), 500

    recommendation = recommend_music(detection["emotion"])

    response_payload = {
        "detected_emotion": detection["emotion"],
        "confidence": detection["confidence"],
        "scores": detection["scores"],
        "face_detected": detection["face_detected"],
        "sampled_frames": detection["sampled_frames"],
        "used_frames": detection["used_frames"],
        "recommendation": recommendation,
    }

    if warning:
        response_payload["warning"] = warning

    return jsonify(response_payload)


@routes.route("/recommend-music/<emotion>", methods=["GET"])
def recommend(emotion):
    return jsonify(recommend_music(emotion))
