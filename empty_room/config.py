"""
Empty Room - Configuration Manager.
Provides atomic writes, schema validation, and cached reads.
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict

from empty_room.constants import DEFAULT_CONFIG, get_config_path

_lock = threading.Lock()
_cached_config: Dict[str, Any] = {}
_cached_mtime: float = 0.0


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize configuration inputs."""
    validated = dict(DEFAULT_CONFIG)
    
    # Enabled flag
    if "enabled" in config:
        validated["enabled"] = bool(config["enabled"])
        
    # Timeout (3s to 3600s)
    if "timeout" in config:
        try:
            val = int(config["timeout"])
            validated["timeout"] = max(3, min(3600, val))
        except (ValueError, TypeError):
            pass
            
    # Strict match (authorized face only)
    if "strict_match" in config:
        validated["strict_match"] = bool(config["strict_match"])
        
    # Confidence threshold for LBPH (lower = stricter match, range 10-150)
    if "confidence_threshold" in config:
        try:
            val = int(config["confidence_threshold"])
            validated["confidence_threshold"] = max(10, min(150, val))
        except (ValueError, TypeError):
            pass
            
    # Camera index
    if "camera_index" in config:
        try:
            val = int(config["camera_index"])
            validated["camera_index"] = max(0, val)
        except (ValueError, TypeError):
            pass
            
    # Frame skip (1 to 30)
    if "frame_skip" in config:
        try:
            val = int(config["frame_skip"])
            validated["frame_skip"] = max(1, min(30, val))
        except (ValueError, TypeError):
            pass
            
    # Resolution
    if "resolution_width" in config:
        try:
            val = int(config["resolution_width"])
            validated["resolution_width"] = max(160, min(1920, val))
        except (ValueError, TypeError):
            pass
            
    if "resolution_height" in config:
        try:
            val = int(config["resolution_height"])
            validated["resolution_height"] = max(120, min(1080, val))
        except (ValueError, TypeError):
            pass
            
    # Web port
    if "web_port" in config:
        try:
            val = int(config["web_port"])
            validated["web_port"] = max(1024, min(65535, val))
        except (ValueError, TypeError):
            pass
            
    # Web host
    if "web_host" in config and isinstance(config["web_host"], str):
        # Strict security: Only allow localhost bindings
        host = config["web_host"].strip()
        if host in ("127.0.0.1", "localhost"):
            validated["web_host"] = host
            
    if "grace_period_alert" in config:
        validated["grace_period_alert"] = bool(config["grace_period_alert"])
        
    return validated


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load configuration from disk with caching and fallback defaults."""
    global _cached_config, _cached_mtime
    config_path = get_config_path()
    
    with _lock:
        if not config_path.is_file():
            # If config does not exist, initialize with defaults
            save_config(DEFAULT_CONFIG)
            _cached_config = dict(DEFAULT_CONFIG)
            return _cached_config
            
        try:
            mtime = config_path.stat().st_mtime
            if not force_reload and _cached_config and mtime == _cached_mtime:
                return dict(_cached_config)
                
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            validated = validate_config(data)
            _cached_config = validated
            _cached_mtime = mtime
            return dict(_cached_config)
        except Exception:
            # Fallback gracefully to default or last known good
            if _cached_config:
                return dict(_cached_config)
            return dict(DEFAULT_CONFIG)


def save_config(new_config: Dict[str, Any]) -> bool:
    """Save configuration atomically to disk."""
    global _cached_config, _cached_mtime
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    validated = validate_config(new_config)
    
    with _lock:
        try:
            # Atomic write via temporary file
            temp_dir = config_path.parent
            with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
                json.dump(validated, tf, indent=2)
                temp_name = tf.name
                
            os.replace(temp_name, config_path)
            _cached_config = validated
            _cached_mtime = config_path.stat().st_mtime
            return True
        except Exception as e:
            if "temp_name" in locals() and os.path.exists(temp_name):
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
            print(f"[ERROR] Failed to save configuration: {e}")
            return False


def update_config(partial_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge and update partial settings into configuration."""
    current = load_config()
    current.update(partial_config)
    save_config(current)
    return current
