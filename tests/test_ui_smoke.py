import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

import ui


class FakeService:
    def __init__(self, port=8765, token="token", shutdown_delay_seconds=15):
        self.port = port
        self.token = token
        self.shutdown_delay_seconds = shutdown_delay_seconds
        self.started = False
        self.stopped = False
        self.cancelled = False
        self.shutdown_requested = False
        self.restarted = False
        self.slept = False

    @property
    def is_running(self):
        return self.started and not self.stopped

    def start(self, host="0.0.0.0"):
        self.started = True

    def stop(self):
        self.stopped = True

    def get_status(self):
        return {
            "ok": True,
            "running": self.is_running,
            "port": self.port,
            "shutdown_delay_seconds": self.shutdown_delay_seconds,
            "last_action": {
                "type": "shutdown",
                "requested_by": "unit-test",
                "requested_at": "2026-03-28 12:00:00",
                "delay_seconds": 15,
            },
            "last_shutdown_request": {
                "type": "shutdown",
                "requested_by": "unit-test",
                "requested_at": "2026-03-28 12:00:00",
                "delay_seconds": 15,
            },
            "last_restart_request": None,
            "last_cancel_request": None,
            "last_sleep_request": None,
            "available_urls": [self.get_primary_url()],
        }

    def get_primary_url(self):
        return f"http://127.0.0.1:{self.port}/?token={self.token}"

    def request_shutdown(self, requester_ip, delay_seconds=None):
        self.shutdown_requested = True
        return delay_seconds or self.shutdown_delay_seconds

    def request_cancel_shutdown(self, requester_ip):
        self.cancelled = True

    def request_restart(self, requester_ip, delay_seconds=None):
        self.restarted = True
        return delay_seconds or self.shutdown_delay_seconds

    def request_sleep(self, requester_ip):
        self.slept = True


class FakeConfigManager:
    def __init__(self, config_path=None):
        self.config = SimpleNamespace(
            port=8765,
            access_token="token",
            auto_start=False,
            start_with_windows=False,
            shutdown_delay_seconds=15,
            bind_host="0.0.0.0",
        )

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.config, key, value)
        return self.config


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @mock.patch.object(ui, "ConfigManager", FakeConfigManager)
    @mock.patch.object(ui, "RemoteShutdownService", FakeService)
    @mock.patch.object(ui, "is_startup_enabled", return_value=False)
    def test_window_can_start_service_and_refresh(self, mocked_startup):
        window = ui.MainWindow()
        window.start_service(show_message=False)
        window.refresh_status()

        self.assertIn("服务运行中", window.status_label.text())
        self.assertIn("安排关机", window.last_request_label.text())
        self.assertIn("http://127.0.0.1", window.url_text.toPlainText())
        self.assertFalse(window.qr_label.pixmap().isNull())
        self.assertEqual(window.shutdown_button.text(), "按倒计时关机")

        window._allow_close = True
        window.close()


if __name__ == "__main__":
    unittest.main()
