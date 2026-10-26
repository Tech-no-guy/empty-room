"""
Legacy core.server bridge to empty_room.server.
"""

from empty_room.server.app import app, run_server

__all__ = ["app", "run_server"]