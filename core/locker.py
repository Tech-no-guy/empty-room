"""
Empty Room - Cross-Platform Screen Locker.
Supports Windows, macOS, and Linux (systemd, X11, Wayland).
"""

import os
import platform
import subprocess
import sys
from typing import Dict, Any


def lock_workstation() -> bool:
    """
    Trigger the native OS lock screen command.
    Returns True if successfully triggered, False otherwise.
    """
    system = platform.system()
    
    if system == "Windows":
        try:
            import ctypes
            # User32 LockWorkStation locks workstation immediately
            result = ctypes.windll.user32.LockWorkStation()
            return bool(result != 0)
        except Exception as e:
            print(f"[LOCKER] Windows lock error: {e}", file=sys.stderr)
            return False

    elif system == "Darwin":
        # macOS options: pmset or CGSession
        commands = [
            ["pmset", "displaysleepnow"],
            ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"],
            ["osascript", "-e", 'tell application "System Events" to sleep']
        ]
        for cmd in commands:
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if res.returncode == 0:
                    return True
            except (FileNotFoundError, PermissionError):
                continue
        return False

    elif system == "Linux":
        # Linux desktop environments (GNOME, KDE, XFCE, Sway, i3, Systemd loginctl)
        commands = [
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "--lock"],
            ["cinnamon-screensaver-command", "--lock"],
            ["qdbus", "org.freedesktop.ScreenSaver", "/ScreenSaver", "Lock"],
            ["swaylock"],
            ["i3lock"]
        ]
        for cmd in commands:
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if res.returncode == 0:
                    return True
            except (FileNotFoundError, PermissionError):
                continue
        return False

    return False


def get_locker_info() -> Dict[str, Any]:
    """Inspect the host system and return locker diagnostic information."""
    system = platform.system()
    release = platform.release()
    return {
        "os": system,
        "release": release,
        "supported": system in ("Windows", "Darwin", "Linux"),
        "method": {
            "Windows": "user32.LockWorkStation",
            "Darwin": "pmset / CGSession",
            "Linux": "loginctl / xdg-screensaver"
        }.get(system, "unknown")
    }


# Backwards compatibility alias
lock_screen = lock_workstation
lock_screen_compat = lock_workstation

