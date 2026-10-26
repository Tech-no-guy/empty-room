"""
Legacy core.detector bridge to empty_room.detector.
"""

from empty_room.detector import start_detector, PresenceDetector
from empty_room.locker import lock_screen_compat as lock_screen

__all__ = ["start_detector", "PresenceDetector", "lock_screen"]