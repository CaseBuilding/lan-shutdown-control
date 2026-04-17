import http.client
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from service import RemoteShutdownService


class RemoteShutdownServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.shutdown_calls: list[int] = []
        self.restart_calls: list[int] = []
        self.cancel_calls = 0
        self.sleep_calls = 0

        def cancel_executor() -> None:
            self.cancel_calls += 1

        def sleep_executor() -> None:
            self.sleep_calls += 1

        self.service = RemoteShutdownService(
            port=0,
            token="test-token",
            shutdown_delay_seconds=12,
            shutdown_executor=self.shutdown_calls.append,
            restart_executor=self.restart_calls.append,
            cancel_shutdown_executor=cancel_executor,
            sleep_executor=sleep_executor,
        )
        self.service.start("127.0.0.1")

    def tearDown(self) -> None:
        self.service.stop()

    def _request(self, method: str, path: str, body: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.service.port, timeout=5)
        headers = {}
        payload = None
        if body is not None:
            payload = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        response_body = response.read()
        connection.close()
        return response.status, response_body

    def test_status_requires_valid_token(self) -> None:
        status, body = self._request("GET", "/api/status")
        self.assertEqual(status, 403)
        self.assertIn("Invalid token", body.decode("utf-8"))

    def test_status_with_valid_token_returns_urls(self) -> None:
        status, body = self._request("GET", "/api/status?token=test-token")
        self.assertEqual(status, 200)
        payload = json.loads(body.decode("utf-8"))
        self.assertTrue(payload["running"])
        self.assertTrue(payload["available_urls"])
        self.assertEqual(payload["shutdown_delay_seconds"], 12)

    def test_shutdown_endpoint_uses_default_delay(self) -> None:
        status, body = self._request("POST", "/api/shutdown", {"token": "test-token"})
        self.assertEqual(status, 202)
        self.assertEqual(self.shutdown_calls, [12])
        payload = json.loads(body.decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["delay_seconds"], 12)

    def test_restart_endpoint_accepts_custom_delay(self) -> None:
        status, body = self._request(
            "POST",
            "/api/restart",
            {"token": "test-token", "delay_seconds": 30},
        )
        self.assertEqual(status, 202)
        self.assertEqual(self.restart_calls, [30])
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(payload["delay_seconds"], 30)
        self.assertIn("重启", payload["message"])

    def test_shutdown_endpoint_rejects_negative_delay(self) -> None:
        status, body = self._request(
            "POST",
            "/api/shutdown",
            {"token": "test-token", "delay_seconds": -1},
        )
        self.assertEqual(status, 400)
        self.assertIn("delay_seconds", body.decode("utf-8"))

    def test_cancel_shutdown_endpoint_calls_executor(self) -> None:
        status, body = self._request("POST", "/api/cancel-shutdown", {"token": "test-token"})
        self.assertEqual(status, 200)
        self.assertEqual(self.cancel_calls, 1)
        payload = json.loads(body.decode("utf-8"))
        self.assertTrue(payload["ok"])

    def test_sleep_endpoint_calls_executor(self) -> None:
        status, body = self._request("POST", "/api/sleep", {"token": "test-token"})
        self.assertEqual(status, 200)
        self.assertEqual(self.sleep_calls, 1)
        payload = json.loads(body.decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertIn("休眠", payload["message"])

    def test_control_page_requires_valid_token(self) -> None:
        status, body = self._request("GET", "/")
        self.assertEqual(status, 403)
        self.assertIn("访问被拒绝", body.decode("utf-8"))

        status, body = self._request("GET", "/?token=test-token")
        self.assertEqual(status, 200)
        page = body.decode("utf-8")
        self.assertIn("安排关机", page)
        self.assertIn("安排重启", page)
        self.assertIn("立即休眠", page)
        self.assertIn("取消关机 / 重启", page)


if __name__ == "__main__":
    unittest.main()
