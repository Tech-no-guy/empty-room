"""
Unit tests for cross-platform screen locker inspection.
"""

import unittest
from empty_room.locker import get_locker_info


class TestLocker(unittest.TestCase):

    def test_locker_info_structure(self):
        info = get_locker_info()
        self.assertIn("os", info)
        self.assertIn("supported", info)
        self.assertIn("method", info)
        self.assertIsInstance(info["supported"], bool)


if __name__ == "__main__":
    unittest.main()
