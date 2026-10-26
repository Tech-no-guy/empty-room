"""
Unit tests for CLI routing.
"""

import unittest
from unittest.mock import patch
from core.cli import main


class TestCLI(unittest.TestCase):

    def test_help_invocation(self):
        with patch("sys.argv", ["empty-room", "help"]):
            with self.assertRaises(SystemExit) as cm:
                # Should either exit 0 or finish cleanly
                main()
            # If sys.exit called, should be 0
            if cm.exception:
                self.assertEqual(cm.exception.code, 0)

    def test_unknown_command(self):
        with patch("sys.argv", ["empty-room", "unknown-command-xyz"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
