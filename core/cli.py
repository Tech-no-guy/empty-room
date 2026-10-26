"""
Empty Room - Smart Screen Lock Command Line Interface.
Dispatches commands:
  empty-room run
  empty-room configure run
  empty-room stop
  empty-room shadow on
  empty-room shadow off
  empty-room status
  empty-room help
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

from core import __version__
from core.config import load_config
from core.constants import FOREGROUND_PID_FILE
from core.daemon import (
    is_shadow_running,
    start_shadow_daemon,
    stop_all,
    stop_shadow_daemon,
)
from core.detector import start_detector
from core.face_engine import FaceEngine
from core.locker import get_locker_info
from core.server.app import run_server

LOGO_ASCII = r"""
     +----------------------------------+
    /                                    \
   |      +------------------------+      |
   |      |                        |      |
   |      |      EMPTY ROOM        |      |
   |      |      SMART LOCK        |      |
   |      |                        |      |
   |      +------------------------+      |
    \                                    /
     +----------------------------------+
"""


def print_banner():
    """Print the terminal banner."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
            
    print("\033[96m" + LOGO_ASCII + "\033[0m")
    print(f" Empty Room -- Smart Screen Lock (v{__version__})")
    print(" Automatically locks your screen when you walk away.\n")


def cmd_run(args=None):
    """Run presence detection in foreground mode."""
    print_banner()
    config = load_config()
    print(f"[*] Mode: Foreground Presence Detection")
    print(f"[*] Auto-Lock Timeout: {config.get('timeout', 10)} seconds")
    print(f"[*] Strict Face Match: {'ENABLED (Authorized Face Only)' if config.get('strict_match') else 'BASIC (Any Person)'}")
    print(f"[*] Camera Device: Index {config.get('camera_index', 0)}")
    print(f"[*] Web Portal: Run 'empty-room configure run' to adjust parameters or train biometrics.")
    print(f"[*] Press Ctrl+C at any time to exit.\n")

    # Record foreground PID
    FOREGROUND_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    FOREGROUND_PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def _sig_handler(sig, frame):
        print("\n[!] Shutdown signal received. Exiting Empty Room.")
        FOREGROUND_PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sig_handler)

    try:
        start_detector()
    finally:
        FOREGROUND_PID_FILE.unlink(missing_ok=True)


def cmd_configure(args=None):
    """Start the configuration web interface and open localhost portal."""
    print_banner()
    config = load_config()
    port = config.get("web_port", 5050)
    host = config.get("web_host", "127.0.0.1")
    
    print(f"[*] Launching Empty Room Configuration Portal...")
    print(f"[*] Local endpoint: http://{host}:{port}")
    print(f"[*] Interactive face enrollment and parameter controls available.")
    print(f"[*] Opening your default browser...\n")
    
    run_server(host=host, port=port, open_browser=True)


def cmd_shadow(subcommand: str):
    """Control background shadow daemon."""
    print_banner()
    if subcommand.lower() in ("on", "start"):
        print("[*] Spawning Empty Room Shadow Daemon...")
        success, message = start_shadow_daemon()
        if success:
            print(f"\033[92m[+] {message}\033[0m")
            print("    The screen lock sentinel is now active in the background.")
            print("    It will continue protecting your screen even when this terminal is closed.")
            print("    Run 'empty-room shadow off' or 'empty-room stop' to terminate.")
        else:
            print(f"\033[91m[X] {message}\033[0m")
            sys.exit(1)

    elif subcommand.lower() in ("off", "stop"):
        print("[*] Stopping Empty Room Shadow Daemon...")
        success, message = stop_shadow_daemon()
        if success:
            print(f"\033[92m[+] {message}\033[0m")
        else:
            print(f"\033[91m[X] {message}\033[0m")
            sys.exit(1)
    else:
        print(f"[!] Unknown shadow action: '{subcommand}'. Use 'on' or 'off'.")
        sys.exit(1)


def cmd_stop():
    """Stop all running Empty Room instances."""
    print_banner()
    print("[*] Halting all active Empty Room processes...")
    success, message = stop_all()
    if success:
        print(f"\033[92m[+] {message}\033[0m")
    else:
        print(f"\033[91m[X] {message}\033[0m")


def cmd_status():
    """Display real-time system and daemon status."""
    print_banner()
    config = load_config()
    face_engine = FaceEngine()
    face_info = face_engine.get_info()
    shadow_active, shadow_pid = is_shadow_running()
    locker_info = get_locker_info()

    print("--- [DAEMON STATUS] ---")
    if shadow_active:
        print(f"  Shadow Background Daemon: \033[92mACTIVE\033[0m (PID: {shadow_pid})")
    else:
        print(f"  Shadow Background Daemon: \033[90mINACTIVE\033[0m")
    print(f"  Python Runtime:           {sys.executable}")

    print("\n--- [CONFIGURATION] ---")
    print(f"  Sentinel Protection:     {'ARMED' if config.get('enabled') else 'DISARMED'}")
    print(f"  Lock Timeout:            {config.get('timeout')} seconds")
    print(f"  Strict Biometric Mode:   {'YES (Authorized User Only)' if config.get('strict_match') else 'NO (Any Person)'}")
    print(f"  Confidence Strictness:   {config.get('confidence_threshold')}")
    print(f"  Webcam Device Index:     {config.get('camera_index')}")

    print("\n--- [BIOMETRIC PROFILE] ---")
    if face_info.get("trained"):
        print(f"  Face Profile:            \033[92mREGISTERED\033[0m")
        print(f"  Enrolled At:             {face_info.get('enrolled_at')}")
        print(f"  Biometric Samples:       {face_info.get('samples_count')}")
    else:
        print(f"  Face Profile:            \033[93mUNREGISTERED\033[0m (Run 'empty-room configure run' to enroll)")

    print("\n--- [PLATFORM LOCKER] ---")
    print(f"  Host Operating System:   {locker_info.get('os')} ({locker_info.get('release')})")
    print(f"  Supported:               {locker_info.get('supported')}")
    print(f"  Lock Engine Mechanism:   {locker_info.get('method')}\n")


def cmd_help():
    """Display comprehensive CLI help guide."""
    print_banner()
    help_text = """
COMMAND REFERENCE:

  empty-room run
      Starts presence detection in the foreground.
      Continuously monitors presence and automatically locks the workstation
      when the desk is unattended. Press Ctrl+C to exit.

  empty-room configure run
      Launches the web configuration dashboard on http://127.0.0.1:5050
      and automatically opens your browser. Allows live camera preview,
      interactive face biometric enrollment/modification, and sensitivity adjustments.

  empty-room shadow on
      Runs Empty Room as an independent background daemon process.
      Survives terminal closure, system re-logins, or SSH sessions.
      Logs activity to ~/.empty-room/shadow.log.

  empty-room shadow off
      Safely halts and cleans up the running background shadow daemon.

  empty-room stop
      Stops all active Empty Room processes across foreground, shadow,
      and configuration server modes.

  empty-room status
      Inspects process tables, biometrics registry, and configuration status.

  empty-room help
      Shows this user guide.

EXAMPLES:
  $ empty-room run                      # Start monitoring now
  $ empty-room configure run            # Open web settings and face registration
  $ empty-room shadow on                # Run silently in background
  $ empty-room status                   # Check whether shadow daemon is active
  $ empty-room stop                     # Stop all instances

SECURITY ARCHITECTURE:
  - Web portal binds strictly to 127.0.0.1 with per-session CSRF tokens.
  - Zero cloud reliance: 100% of biometric processing and vision inference
    remains local and private on device.
  - Fail-safe atomic writes protect configuration integrity.
"""
    print(help_text)


def _daemon_worker():
    """Internal entrypoint executed in detached background shadow mode."""
    try:
        start_detector()
    except Exception:
        import traceback
        from core.constants import SHADOW_LOG_FILE
        with open(str(SHADOW_LOG_FILE), "a", encoding="utf-8") as f:
            f.write("\n--- DAEMON CRASH EXCEPTION ---\n")
            traceback.print_exc(file=f)


def main():
    """Main CLI argument router."""
    argv = sys.argv[1:]
    if not argv:
        cmd_help()
        sys.exit(0)

    cmd = argv[0].lower()

    if cmd == "run":
        cmd_run(argv[1:])
    elif cmd in ("configure", "config"):
        # Support both 'empty-room configure run' and 'empty-room configure'
        cmd_configure(argv[1:])
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "shadow":
        if len(argv) < 2:
            print("[!] Please specify 'on' or 'off'. Example: 'empty-room shadow on'")
            sys.exit(1)
        cmd_shadow(argv[1])
    elif cmd == "status":
        cmd_status()
    elif cmd in ("help", "--help", "-h"):
        cmd_help()
        sys.exit(0)
    elif cmd == "_daemon_worker":
        _daemon_worker()
    else:
        print(f"[!] Unknown command: '{cmd}'. Run 'empty-room help' for available commands.")
        sys.exit(1)


if __name__ == "__main__":
    main()
