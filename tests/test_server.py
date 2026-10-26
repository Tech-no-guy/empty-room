"""
Unit and integration tests for the Flask configuration server.
"""

import json
import unittest
from empty_room.server.app import app, CSRF_TOKEN


class TestServer(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_dashboard_renders(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("EMPTY ROOM", html)
        self.assertIn("Presence Sentinel", html)
        self.assertIn("logo.svg", html)

    def test_security_headers(self):
        res = self.client.get("/")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn("default-src 'self'", res.headers.get("Content-Security-Policy", ""))

    def test_get_status(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("telemetry", data)
        self.assertIn("face", data)

    def test_get_config(self):
        res = self.client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("timeout", data["config"])

    def test_csrf_protection_rejection(self):
        # State-modifying POST without CSRF token should return 403 Forbidden
        res = self.client.post("/api/config", json={"timeout": 25})
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data.get("success"))

    def test_csrf_authorized_update(self):
        # State-modifying POST with valid CSRF token should succeed
        res = self.client.post(
            "/api/config",
            json={"timeout": 20},
            headers={"X-CSRF-Token": CSRF_TOKEN}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["config"]["timeout"], 20)

    def test_logs_endpoint(self):
        res = self.client.get("/api/logs")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("logs"), list)


if __name__ == "__main__":
    unittest.main()
