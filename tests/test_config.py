"""
Unit tests for configuration manager and atomic persistence.
"""

import os
import tempfile
import unittest
from pathlib import Path

from core.config import load_config, save_config, update_config, validate_config
from core.constants import DEFAULT_CONFIG


class TestConfig(unittest.TestCase):

    def test_validate_defaults(self):
        result = validate_config({})
        self.assertEqual(result["timeout"], DEFAULT_CONFIG["timeout"])
        self.assertEqual(result["enabled"], DEFAULT_CONFIG["enabled"])
        self.assertEqual(result["strict_match"], DEFAULT_CONFIG["strict_match"])

    def test_validate_bounds(self):
        # Timeout below minimum
        result = validate_config({"timeout": 1})
        self.assertEqual(result["timeout"], 3)

        # Timeout above maximum
        result = validate_config({"timeout": 99999})
        self.assertEqual(result["timeout"], 3600)

        # Confidence bounds
        result = validate_config({"confidence_threshold": 5})
        self.assertEqual(result["confidence_threshold"], 10)

        result = validate_config({"confidence_threshold": 200})
        self.assertEqual(result["confidence_threshold"], 150)

    def test_security_host_validation(self):
        # Disallow non-localhost bindings
        result = validate_config({"web_host": "0.0.0.0"})
        self.assertEqual(result["web_host"], "127.0.0.1")

        result = validate_config({"web_host": "192.168.1.100"})
        self.assertEqual(result["web_host"], "127.0.0.1")

        # Allow localhost
        result = validate_config({"web_host": "localhost"})
        self.assertEqual(result["web_host"], "localhost")

    def test_atomic_save_and_load(self):
        cfg = load_config()
        original_timeout = cfg.get("timeout", 10)
        try:
            update_config({"timeout": 45})
            reloaded = load_config(force_reload=True)
            self.assertEqual(reloaded["timeout"], 45)
        finally:
            update_config({"timeout": original_timeout})


if __name__ == "__main__":
    unittest.main()
