"""
Empty Room - Presence Detection Engine.
Monitors the webcam feed, identifies authorized presence, manages timeout countdowns,
and executes workstation lock.
"""

import collections
import datetime
import threading
import time
from typing import Any, Dict, List, Optional

import cv2

from empty_room.camera import CameraService
from empty_room.config import load_config
from empty_room.face_engine import FaceEngine
from empty_room.locker import lock_workstation


class PresenceDetector:
    """Core presence detection daemon engine."""

    def __init__(self):
        self.camera_service = CameraService.get_instance()
        self.face_engine = FaceEngine()
        self.is_running = False
        self._stop_event = threading.Event()
        
        # Runtime Telemetry State
        self.state = "INITIALIZING"
        self.time_away = 0.0
        self.seconds_remaining = 0.0
        self.authorized_present = False
        self.last_seen = time.time()
        self.last_lock_time: Optional[float] = None
        self.faces_count = 0
        self.latest_faces: List[Dict[str, Any]] = []
        self.status_message = "Initializing detection engine..."
        
        # Thread-safe event log buffer (last 50 events)
        self.events_log = collections.deque(maxlen=50)
        self._state_lock = threading.Lock()
        
        self.log_event("SYSTEM", "Presence detector engine initialized.")

    def log_event(self, category: str, message: str):
        """Append an event to the internal audit trail."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": timestamp,
            "category": category,
            "message": message
        }
        with self._state_lock:
            self.events_log.appendleft(entry)
        try:
            print(f"[{timestamp}] [{category}] {message}", flush=True)
        except Exception:
            pass

    def get_telemetry(self) -> Dict[str, Any]:
        """Return real-time state for API and CLI."""
        with self._state_lock:
            config = load_config()
            timeout = config.get("timeout", 10)
            
            return {
                "state": self.state,
                "enabled": config.get("enabled", True),
                "strict_match": config.get("strict_match", False),
                "timeout": timeout,
                "time_away": round(self.time_away, 1),
                "seconds_remaining": max(0.0, round(self.seconds_remaining, 1)),
                "authorized_present": self.authorized_present,
                "faces_detected": self.faces_count,
                "camera_fps": self.camera_service.fps,
                "status_message": self.status_message,
                "face_model_trained": self.face_engine.is_trained(),
                "last_lock_time": self.last_lock_time,
                "latest_faces": list(self.latest_faces)
            }

    def get_events(self) -> List[Dict[str, str]]:
        """Return copies of recent event logs."""
        with self._state_lock:
            return list(self.events_log)

    def start(self, camera_index: Optional[int] = None):
        """Start presence detection loop."""
        self.is_running = True
        self._stop_event.clear()
        
        config = load_config()
        self.log_event("STARTUP", f"Starting Empty Room presence detector (Timeout: {config.get('timeout', 10)}s)")
        
        if not self.camera_service.start(camera_index):
            self.state = "ERROR"
            self.status_message = "Failed to access webcam."
            self.log_event("ERROR", "Webcam device could not be opened.")
            return

        self.last_seen = time.time()
        skip_counter = 0

        try:
            while not self._stop_event.is_set():
                config = load_config()
                if not config.get("enabled", True):
                    with self._state_lock:
                        self.state = "DISABLED"
                        self.status_message = "Auto-lock is paused in configuration."
                        self.time_away = 0.0
                        self.seconds_remaining = config.get("timeout", 10)
                    time.sleep(1.0)
                    self.last_seen = time.time()
                    continue

                success, frame = self.camera_service.read_frame()
                if not success or frame is None:
                    time.sleep(0.05)
                    continue

                skip_counter += 1
                frame_skip = config.get("frame_skip", 5)
                if skip_counter % frame_skip != 0:
                    time.sleep(0.02)
                    continue

                # Process frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_boxes = self.face_engine.detect_faces(gray)
                
                authorized_found = False
                detected_info = []
                strict_match = config.get("strict_match", False)
                confidence_thresh = config.get("confidence_threshold", 75)

                for (x, y, w, h) in face_boxes:
                    face_crop = gray[y:y+h, x:x+w]
                    
                    if strict_match and self.face_engine.is_trained():
                        is_auth, dist = self.face_engine.verify_face(face_crop, threshold=confidence_thresh)
                        if is_auth:
                            authorized_found = True
                        detected_info.append({
                            "box": [x, y, w, h],
                            "authorized": is_auth,
                            "distance": round(dist, 1)
                        })
                    else:
                        # Basic presence mode: any human face counts as present
                        authorized_found = True
                        detected_info.append({
                            "box": [x, y, w, h],
                            "authorized": True,
                            "distance": 0.0
                        })

                now = time.time()
                timeout = config.get("timeout", 10)

                with self._state_lock:
                    self.faces_count = len(face_boxes)
                    self.latest_faces = detected_info
                    self.authorized_present = authorized_found

                    if authorized_found:
                        if self.state in ("AWAY", "LOCKED"):
                            self.log_event("PRESENCE", "Authorized user detected. Timer reset.")
                        self.state = "PRESENT"
                        self.last_seen = now
                        self.time_away = 0.0
                        self.seconds_remaining = float(timeout)
                        self.status_message = "User present. Workstation protected."
                    else:
                        self.time_away = now - self.last_seen
                        self.seconds_remaining = max(0.0, timeout - self.time_away)
                        
                        if self.seconds_remaining <= 0.0:
                            self.state = "LOCKED"
                            self.status_message = "Room empty. Locking workstation now."
                        elif self.seconds_remaining <= 3.0:
                            self.state = "WARNING"
                            self.status_message = f"Warning: Locking workstation in {round(self.seconds_remaining, 1)}s..."
                        else:
                            self.state = "AWAY"
                            self.status_message = f"Presence lost. Locking in {round(self.seconds_remaining, 1)}s."

                # Execute lock if timeout expired
                if self.seconds_remaining <= 0.0:
                    self.log_event("LOCK", f"Timeout reached ({timeout}s). Initiating workstation lock.")
                    lock_success = lock_workstation()
                    self.last_lock_time = time.time()
                    if lock_success:
                        self.log_event("LOCK", "Native lock screen triggered successfully.")
                    else:
                        self.log_event("WARN", "Lock screen command returned non-zero or unsupported.")

                    # Cooldown pause to prevent spamming lock calls while system is locked
                    time.sleep(4.0)
                    self.last_seen = time.time()

                time.sleep(0.04)

        except KeyboardInterrupt:
            self.log_event("SHUTDOWN", "Presence detector received interrupt signal.")
        finally:
            self.stop()

    def stop(self):
        """Cleanly stop detection and release resources."""
        self._stop_event.set()
        self.is_running = False
        self.state = "STOPPED"
        self.status_message = "Presence detector stopped."
        self.camera_service.stop()
        self.log_event("SHUTDOWN", "Presence detector terminated.")


# Module singleton for sharing state with Flask server
_detector_instance: Optional[PresenceDetector] = None
_detector_lock = threading.Lock()

def get_detector() -> PresenceDetector:
    global _detector_instance
    with _detector_lock:
        if _detector_instance is None:
            _detector_instance = PresenceDetector()
        return _detector_instance


def start_detector(camera_index: Optional[int] = None):
    """Convenience launcher for detector."""
    detector = get_detector()
    detector.start(camera_index)
