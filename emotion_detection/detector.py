# emotion_detection/detector.py

import cv2

from app.utils import detect_emotion_details_from_frame


def detect_emotion(frame):
    """
    Detect dominant emotion from a video frame.
    """

    return detect_emotion_details_from_frame(frame)["emotion"]


def start_webcam_detection():
    """
    Start webcam and detect emotion in real-time.
    """

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        details = detect_emotion_details_from_frame(frame)
        emotion = details["emotion"]
        confidence = int(details["confidence"] * 100) if details["face_detected"] else 0

        cv2.putText(
            frame,
            f"Emotion: {emotion} ({confidence}%)",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
