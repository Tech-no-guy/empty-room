"""
Empty Room - Shadow Daemon Manager.
Runs Empty Room in the background detached from the controlling terminal,
surviving terminal closures.
"""

import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from empty_room.constants import (
    FOREGROUND_PID_FILE,
    SERVER_PID_FILE,
    SHADOW_LOG_FILE,
    SHADOW_PID_FILE,
)


def _is_pid_alive(pid: int) -> bool:
    """Check whether a process with the given PID is actively running."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_shadow_pid() -> Optional[int]:
    """Read the active shadow daemon PID or return None if not running."""
    if not SHADOW_PID_FILE.is_file():
        return None
    try:
        content = SHADOW_PID_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return None
        pid = int(content)
        if _is_pid_alive(pid):
            return pid
        # Stale PID file
        SHADOW_PID_FILE.unlink(missing_ok=True)
        return None
    except Exception:
        SHADOW_PID_FILE.unlink(missing_ok=True)
        return None


def is_shadow_running() -> Tuple[bool, Optional[int]]:
    """Return (is_running, pid)."""
    pid = get_shadow_pid()
    return (pid is not None), pid


def start_shadow_daemon() -> Tuple[bool, str]:
    """
    Start Empty Room in shadow mode (detached background daemon).
    Returns (success, message).
    """
    running, existing_pid = is_shadow_running()
    if running:
        return False, f"Shadow daemon is already active (PID: {existing_pid})."

    # Prepare log output
    SHADOW_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SHADOW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n--- Empty Room Shadow Daemon starting at {time.ctime()} ---\n")

    # Inheritable OS file descriptor for detached process
    log_fd = os.open(str(SHADOW_LOG_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND)

    python_exe = sys.executable
    cmd = [python_exe, "-m", "empty_room.cli", "_daemon_worker"]

    from empty_room.constants import PROJECT_ROOT

    env = os.environ.copy()
    current_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}{current_pp}" if current_pp else str(PROJECT_ROOT)

    try:
        if platform.system() == "Windows":
            # Windows detached background process flags
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                cmd,
                stdout=log_fd,
                stderr=log_fd,
                stdin=subprocess.DEVNULL,
                creationflags=flags,
                cwd=str(PROJECT_ROOT),
                env=env
            )
        else:
            # POSIX detached process
            proc = subprocess.Popen(
                cmd,
                stdout=log_fd,
                stderr=log_fd,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                cwd=str(PROJECT_ROOT),
                env=env,
                close_fds=True
            )
        # Record PID
        SHADOW_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        SHADOW_PID_FILE.write_text(str(proc.pid), encoding="utf-8")

        # Verify it started successfully
        time.sleep(0.5)
        if proc.poll() is not None:
            return False, f"Shadow daemon failed to start. Review log at {SHADOW_LOG_FILE}"

        return True, f"Shadow daemon started successfully (PID: {proc.pid}). Running in background."

    except Exception as e:
        return False, f"Failed to spawn shadow daemon: {e}"
    finally:
        try:
            os.close(log_fd)
        except OSError:
            pass


def _terminate_pid(pid: int) -> bool:
    """Terminate a process by PID cleanly."""
    if not _is_pid_alive(pid):
        return True

    if platform.system() == "Windows":
        try:
            # Terminate process tree
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            # Wait up to 2 seconds for process and camera handles to unload
            for _ in range(10):
                if not _is_pid_alive(pid):
                    return True
                time.sleep(0.2)
            return not _is_pid_alive(pid)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
                return True
            except OSError:
                return not _is_pid_alive(pid)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(15):
                if not _is_pid_alive(pid):
                    return True
                time.sleep(0.1)
            # Force kill if still alive
            os.kill(pid, signal.SIGKILL)
            return True
        except Exception:
            return False


def stop_shadow_daemon() -> Tuple[bool, str]:
    """Stop the shadow daemon."""
    running, pid = is_shadow_running()
    if not running or pid is None:
        SHADOW_PID_FILE.unlink(missing_ok=True)
        return True, "Shadow daemon is not running."

    success = _terminate_pid(pid)
    SHADOW_PID_FILE.unlink(missing_ok=True)
    if success:
        return True, f"Shadow daemon (PID: {pid}) stopped successfully."
    else:
        return False, f"Failed to stop shadow daemon (PID: {pid})."


def stop_all() -> Tuple[bool, str]:
    """Stop all running Empty Room instances (shadow daemon, foreground, server)."""
    messages = []
    
    # 1. Shadow daemon
    running, shadow_pid = is_shadow_running()
    if running and shadow_pid:
        _terminate_pid(shadow_pid)
        SHADOW_PID_FILE.unlink(missing_ok=True)
        messages.append(f"Stopped shadow daemon (PID {shadow_pid})")

    # 2. Foreground detector PID
    if FOREGROUND_PID_FILE.is_file():
        try:
            fg_pid = int(FOREGROUND_PID_FILE.read_text(encoding="utf-8").strip())
            if _is_pid_alive(fg_pid):
                _terminate_pid(fg_pid)
                messages.append(f"Stopped foreground detector (PID {fg_pid})")
        except Exception:
            pass
        FOREGROUND_PID_FILE.unlink(missing_ok=True)

    # 3. Server PID
    if SERVER_PID_FILE.is_file():
        try:
            srv_pid = int(SERVER_PID_FILE.read_text(encoding="utf-8").strip())
            if _is_pid_alive(srv_pid):
                _terminate_pid(srv_pid)
                messages.append(f"Stopped configuration server (PID {srv_pid})")
        except Exception:
            pass
        SERVER_PID_FILE.unlink(missing_ok=True)

    if not messages:
        return True, "No active Empty Room instances were running."
    return True, "; ".join(messages) + "."
