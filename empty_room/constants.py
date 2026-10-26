"""
Empty Room - Constants and Configuration Paths.
"""

import os
from pathlib import Path
import cv2

# Base data directory: user home directory or environment override
HOME_DIR = Path(os.environ.get("EMPTY_ROOM_HOME", Path.home() / ".empty-room"))
HOME_DIR.mkdir(parents=True, exist_ok=True)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration files
# If config.json exists in current working dir, use it; otherwise use HOME_DIR / "config.json"
CWD_CONFIG = Path.cwd() / "config.json"
USER_CONFIG = HOME_DIR / "config.json"

def get_config_path() -> Path:
    """Return the active configuration file path."""
    if CWD_CONFIG.is_file():
        return CWD_CONFIG
    return USER_CONFIG

# Face recognition model path
CWD_MODEL = Path.cwd() / "face_model.yml"
USER_MODEL = HOME_DIR / "face_model.yml"

def get_model_path() -> Path:
    """Return the active face model path."""
    if CWD_MODEL.is_file():
        return CWD_MODEL
    return USER_MODEL

# Haar cascade file resolution
def get_cascade_path() -> str:
    """Find and return the valid Haar cascade xml path."""
    candidates = [
        PROJECT_ROOT / "data" / "haarcascade_frontalface_default.xml",
        Path.cwd() / "haarcascade_frontalface_default.xml",
        PROJECT_ROOT / "haarcascade_frontalface_default.xml",
        HOME_DIR / "haarcascade_frontalface_default.xml",
    ]
    for p in candidates:
        if p.is_file():
            return str(p.resolve())
            
    # Fallback to OpenCV built-in cascades
    if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
        builtin = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.isfile(builtin):
            return builtin
            
    # Default to filename and let cv2 resolve
    return "haarcascade_frontalface_default.xml"

# Runtime PID and Log files
PID_DIR = HOME_DIR / "run"
PID_DIR.mkdir(parents=True, exist_ok=True)

SHADOW_PID_FILE = PID_DIR / "shadow.pid"
FOREGROUND_PID_FILE = PID_DIR / "detector.pid"
SERVER_PID_FILE = PID_DIR / "server.pid"
SHADOW_LOG_FILE = HOME_DIR / "shadow.log"
APP_LOG_FILE = HOME_DIR / "empty_room.log"

# Default application settings
DEFAULT_CONFIG = {
    "enabled": True,
    "timeout": 10,
    "strict_match": False,
    "confidence_threshold": 75,
    "camera_index": 0,
    "frame_skip": 5,
    "resolution_width": 320,
    "resolution_height": 240,
    "web_port": 5050,
    "web_host": "127.0.0.1",
    "grace_period_alert": True
}
