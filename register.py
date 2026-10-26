"""
Empty Room - Legacy Registration Entrypoint (register.py).
Maintained for backwards compatibility; uses secure FaceEngine.
"""

import sys
import time
import cv2
import numpy as np

from core.constants import get_cascade_path
from core.face_engine import FaceEngine


def register_face():
    """Terminal-based face registration."""
    print("=" * 60)
    print("  Empty Room - Biometric Face Registration")
    print("=" * 60)
    print("\nTip: You can also use 'empty-room configure run' for the interactive web portal.\n")

    cascade_path = get_cascade_path()
    face_cascade = cv2.CascadeClassifier(cascade_path)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return False

    faces_data = []
    print("[*] Look directly at the camera. Beginning capture in 3 seconds...")
    time.sleep(3.0)

    count = 0
    target = 50
    print("[*] Capturing 50 samples. Slowly move your head slightly...")

    while count < target:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))

        for (x, y, w, h) in faces:
            count += 1
            faces_data.append(gray[y:y+h, x:x+w])
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Samples: {count}/{target}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            break

        cv2.imshow("Empty Room - Registering Biometrics (ESC to cancel)", frame)
        key = cv2.waitKey(60) & 0xFF
        if key == 27:  # ESC
            print("\n[!] Registration aborted by user.")
            cap.release()
            cv2.destroyAllWindows()
            return False

    cap.release()
    cv2.destroyAllWindows()

    print("\n[*] Training biometric recognizer...")
    engine = FaceEngine()
    success = engine.train(faces_data, label_id=1)
    if success:
        print("[+] Success! Biometric model trained and saved.")
        return True
    else:
        print("[!] Biometric training encountered an error.")
        return False


if __name__ == '__main__':
    register_face()