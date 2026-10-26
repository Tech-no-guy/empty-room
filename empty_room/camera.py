"""
Empty Room - Thread-Safe Camera Manager and Frame Broker.
Provides non-blocking access to webcam frames for both detector and web streaming.
"""

import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from empty_room.config import load_config


class CameraService:
    """Singleton service providing thread-safe webcam access."""
    _instance: Optional["CameraService"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "CameraService":
        with cls._lock:
            if cls._instance is None:
                cls._instance = CameraService()
            return cls._instance

    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.active_camera_index: int = 0
        self.is_running: bool = False
        self.last_frame: Optional[np.ndarray] = None
        self.last_frame_time: float = 0.0
        self.thread: Optional[threading.Thread] = None
        self._frame_lock = threading.Lock()
        self.fps: float = 0.0
        self._frame_count: int = 0
        self._fps_start: float = time.time()

    def start(self, camera_index: Optional[int] = None) -> bool:
        """Start the background camera capture thread."""
        config = load_config()
        if camera_index is None:
            camera_index = config.get("camera_index", 0)

        with self._frame_lock:
            if self.is_running and self.cap is not None and self.active_camera_index == camera_index:
                return True

            self.stop()
            self.active_camera_index = camera_index
            
            # Open video capture with OS-appropriate backend (CAP_DSHOW on Windows for instant capture)
            import platform
            backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

            self.cap = cv2.VideoCapture(camera_index, backend)
            if not self.cap.isOpened():
                # Try fallback default index 0 or standard backend
                if camera_index != 0:
                    self.cap = cv2.VideoCapture(0, backend)
                    self.active_camera_index = 0
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(camera_index)

            if not self.cap or not self.cap.isOpened():
                print(f"[CAMERA] Unable to open camera device {camera_index}")
                return False

            width = config.get("resolution_width", 320)
            height = config.get("resolution_height", 240)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True

    def _capture_loop(self):
        """Continuously grab the latest camera frame."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            with self._frame_lock:
                self.last_frame = frame
                self.last_frame_time = time.time()
                self._frame_count += 1
                
                # Update FPS every 10 frames
                now = time.time()
                elapsed = now - self._fps_start
                if elapsed >= 1.0:
                    self.fps = round(self._frame_count / elapsed, 1)
                    self._frame_count = 0
                    self._fps_start = now

            # Sleep slightly to prevent 100% CPU usage on frame capture
            time.sleep(0.015)

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Retrieve the latest frame in a thread-safe manner."""
        with self._frame_lock:
            if not self.is_running or self.last_frame is None:
                return False, None
            return True, self.last_frame.copy()

    def stop(self):
        """Stop background capture and release the webcam hardware."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None

        with self._frame_lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.last_frame = None
            self.fps = 0.0
