from __future__ import annotations

import ctypes
import ipaddress
import json
import os
import secrets
import socket
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlparse


def generate_access_token() -> str:
    return secrets.token_urlsafe(24)


def _ensure_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("This project currently supports Windows power actions only.")


def _spawn_windows_command(command: list[str]) -> None:
    _ensure_windows()
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(command, creationflags=creation_flags)


def default_shutdown_executor(delay_seconds: int) -> None:
    seconds = max(0, int(delay_seconds))
    _spawn_windows_command(
        [
            "shutdown",
            "/s",
            "/t",
            str(seconds),
            "/c",
            "LAN remote shutdown",
        ]
    )


def default_restart_executor(delay_seconds: int) -> None:
    seconds = max(0, int(delay_seconds))
    _spawn_windows_command(
        [
            "shutdown",
            "/r",
            "/t",
            str(seconds),
            "/c",
            "LAN remote restart",
        ]
    )


def default_cancel_shutdown_executor() -> None:
    _spawn_windows_command(["shutdown", "/a"])


def default_sleep_executor() -> None:
    _ensure_windows()
    result = ctypes.windll.powrprof.SetSuspendState(False, False, False)
    if result == 0:
        raise RuntimeError("Failed to put Windows into sleep mode.")


def _safe_ip_sort_key(ip_text: str) -> tuple[int, str]:
    ip_value = ipaddress.ip_address(ip_text)
    return (1 if ip_value.is_loopback else 0, ip_text)


def discover_local_ipv4_addresses() -> list[str]:
    addresses: set[str] = set()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            addresses.add(sock.getsockname()[0])
    except OSError:
        pass

    hostname = socket.gethostname()
    try:
        host_addresses = socket.gethostbyname_ex(hostname)[2]
    except OSError:
        host_addresses = []

    for ip_text in host_addresses:
        try:
            ip_value = ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        if isinstance(ip_value, ipaddress.IPv4Address):
            addresses.add(ip_text)

    if not addresses:
        addresses.add("127.0.0.1")

    return sorted(addresses, key=_safe_ip_sort_key)


class RemoteShutdownService:
    def __init__(
        self,
        port: int = 8765,
        token: str | None = None,
        shutdown_delay_seconds: int = 15,
        shutdown_executor: Callable[[int], None] = default_shutdown_executor,
        restart_executor: Callable[[int], None] = default_restart_executor,
        cancel_shutdown_executor: Callable[[], None] = default_cancel_shutdown_executor,
        sleep_executor: Callable[[], None] = default_sleep_executor,
    ) -> None:
        self.host = "0.0.0.0"
        self.port = int(port)
        self.token = token or generate_access_token()
        self.shutdown_delay_seconds = int(shutdown_delay_seconds)
        self.shutdown_executor = shutdown_executor
        self.restart_executor = restart_executor
        self.cancel_shutdown_executor = cancel_shutdown_executor
        self.sleep_executor = sleep_executor

        self._lock = threading.RLock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._started_at: float | None = None
        self._last_action: dict[str, object] | None = None
        self._last_shutdown_request: dict[str, object] | None = None
        self._last_restart_request: dict[str, object] | None = None
        self._last_cancel_request: dict[str, object] | None = None
        self._last_sleep_request: dict[str, object] | None = None

    @property
    def is_running(self) -> bool:
        return self._server is not None and self._thread is not None and self._thread.is_alive()

    def start(self, host: str = "0.0.0.0") -> None:
        with self._lock:
            if self.is_running:
                return

            self.host = host
            handler_class = self._build_handler()
            self._server = ThreadingHTTPServer((host, self.port), handler_class)
            self._server.daemon_threads = True
            self.port = int(self._server.server_address[1])

            self._thread = threading.Thread(
                target=self._server.serve_forever,
                name="RemoteShutdownHttpServer",
                daemon=True,
            )
            self._thread.start()
            self._started_at = time.time()

    def stop(self) -> None:
        with self._lock:
            if not self._server:
                return

            self._server.shutdown()
            self._server.server_close()
            self._server = None

            if self._thread:
                self._thread.join(timeout=2)
            self._thread = None

    def request_shutdown(self, requester_ip: str, delay_seconds: int | None = None) -> int:
        seconds = self._normalize_delay(delay_seconds)
        self.shutdown_executor(seconds)
        action = self._record_action("shutdown", requester_ip, delay_seconds=seconds)
        self._last_shutdown_request = action
        return seconds

    def request_restart(self, requester_ip: str, delay_seconds: int | None = None) -> int:
        seconds = self._normalize_delay(delay_seconds)
        self.restart_executor(seconds)
        action = self._record_action("restart", requester_ip, delay_seconds=seconds)
        self._last_restart_request = action
        return seconds

    def request_cancel_shutdown(self, requester_ip: str) -> None:
        self.cancel_shutdown_executor()
        action = self._record_action("cancel_shutdown", requester_ip)
        self._last_cancel_request = action

    def request_sleep(self, requester_ip: str) -> None:
        self.sleep_executor()
        action = self._record_action("sleep", requester_ip)
        self._last_sleep_request = action

    def is_authorized(self, token: str) -> bool:
        return bool(token) and secrets.compare_digest(token, self.token)

    def get_status(self) -> dict[str, object]:
        return {
            "ok": True,
            "running": self.is_running,
            "port": self.port,
            "shutdown_delay_seconds": self.shutdown_delay_seconds,
            "started_at": self._started_at,
            "last_action": self._last_action,
            "last_shutdown_request": self._last_shutdown_request,
            "last_restart_request": self._last_restart_request,
            "last_cancel_request": self._last_cancel_request,
            "last_sleep_request": self._last_sleep_request,
            "available_urls": self.get_access_urls(),
        }

    def get_access_urls(self) -> list[str]:
        return [
            f"http://{ip_text}:{self.port}/?token={self.token}"
            for ip_text in discover_local_ipv4_addresses()
        ]

    def get_primary_url(self) -> str:
        for url in self.get_access_urls():
            if "127.0.0.1" not in url:
                return url
        urls = self.get_access_urls()
        return urls[0] if urls else ""

    def render_control_page(self) -> str:
        default_delay = int(self.shutdown_delay_seconds)
        token_text = json.dumps(self.token)
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>局域网电脑控制</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #eef3f8;
      --panel: rgba(255, 255, 255, 0.96);
      --text: #182536;
      --muted: #607084;
      --line: #d5ddeb;
      --primary: #1f62d1;
      --primary-hover: #184fa8;
      --danger: #cf3d3d;
      --danger-hover: #a72f2f;
      --neutral: #43546a;
      --neutral-hover: #334153;
      --success: #2f7d55;
      --success-hover: #235f40;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
      background:
        radial-gradient(circle at top left, #ffffff 0%, #f3f7fc 48%, #e8eef7 100%);
      color: var(--text);
    }}
    .wrap {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 20px;
    }}
    .card {{
      width: min(100%, 520px);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 22px 60px rgba(19, 37, 69, 0.14);
      backdrop-filter: blur(12px);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 30px;
    }}
    p {{
      margin: 0 0 14px;
      line-height: 1.65;
      color: var(--muted);
    }}
    label {{
      display: block;
      margin: 18px 0 8px;
      font-size: 15px;
      font-weight: 700;
    }}
    input {{
      width: 100%;
      padding: 14px 16px;
      border-radius: 14px;
      border: 1px solid var(--line);
      font-size: 18px;
      background: #fff;
    }}
    .button-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 18px;
    }}
    button {{
      border: none;
      border-radius: 16px;
      padding: 15px 16px;
      color: #fff;
      font-size: 17px;
      font-weight: 700;
      cursor: pointer;
    }}
    button:disabled {{
      background: #bcc6d6 !important;
      cursor: wait;
    }}
    .primary {{
      background: var(--danger);
    }}
    .primary:hover {{
      background: var(--danger-hover);
    }}
    .secondary {{
      background: var(--primary);
    }}
    .secondary:hover {{
      background: var(--primary-hover);
    }}
    .neutral {{
      background: var(--neutral);
    }}
    .neutral:hover {{
      background: var(--neutral-hover);
    }}
    .success {{
      background: var(--success);
    }}
    .success:hover {{
      background: var(--success-hover);
    }}
    .status {{
      min-height: 24px;
      margin-top: 18px;
      font-size: 14px;
      line-height: 1.5;
    }}
    .hint {{
      margin-top: 16px;
      font-size: 13px;
      color: var(--muted);
    }}
    code {{
      font-family: Consolas, monospace;
      background: #f2f5f9;
      padding: 2px 5px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>控制这台电脑</h1>
      <p>手机和电脑在同一个局域网时，可以在这里安排关机、安排重启，或者立即让电脑进入休眠。</p>
      <p>下面的倒计时会同时用于关机和重启。休眠是立即执行，不使用倒计时。</p>

      <label for="delayInput">关机 / 重启倒计时（秒）</label>
      <input id="delayInput" type="number" min="0" step="1" value="{default_delay}">

      <div class="button-grid">
        <button id="shutdownButton" class="primary">安排关机</button>
        <button id="restartButton" class="secondary">安排重启</button>
        <button id="cancelButton" class="neutral">取消关机 / 重启</button>
        <button id="sleepButton" class="success">立即休眠</button>
      </div>

      <div id="status" class="status"></div>
      <div class="hint">如果你在电脑旁边，也可以手动执行 <code>shutdown /a</code> 取消当前倒计时。</div>
    </div>
  </div>
  <script>
    const token = {token_text};
    const delayInput = document.getElementById("delayInput");
    const shutdownButton = document.getElementById("shutdownButton");
    const restartButton = document.getElementById("restartButton");
    const cancelButton = document.getElementById("cancelButton");
    const sleepButton = document.getElementById("sleepButton");
    const statusNode = document.getElementById("status");
    const allButtons = [shutdownButton, restartButton, cancelButton, sleepButton];

    function setButtonsDisabled(disabled) {{
      allButtons.forEach((button) => {{
        button.disabled = disabled;
      }});
    }}

    async function postJson(path, payload) {{
      const response = await fetch(path, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload)
      }});
      const result = await response.json();
      if (!response.ok) {{
        throw new Error(result.error || "请求失败");
      }}
      return result;
    }}

    function readDelay() {{
      const delaySeconds = Number.parseInt(delayInput.value, 10);
      if (!Number.isInteger(delaySeconds) || delaySeconds < 0) {{
        throw new Error("请输入 0 或更大的整数秒数。");
      }}
      return delaySeconds;
    }}

    async function runTimedAction(path, confirmText, loadingText) {{
      let delaySeconds;
      try {{
        delaySeconds = readDelay();
      }} catch (error) {{
        statusNode.textContent = error.message;
        return;
      }}

      if (!window.confirm(confirmText.replace("{{delay}}", String(delaySeconds)))) {{
        return;
      }}

      setButtonsDisabled(true);
      statusNode.textContent = loadingText;

      try {{
        const payload = await postJson(path, {{
          token,
          delay_seconds: delaySeconds
        }});
        statusNode.textContent = payload.message || "操作指令已发送。";
      }} catch (error) {{
        statusNode.textContent = "发送失败：" + error.message;
      }} finally {{
        setButtonsDisabled(false);
      }}
    }}

    shutdownButton.addEventListener("click", async () => {{
      await runTimedAction("/api/shutdown", "确定要在 {{delay}} 秒后关机吗？", "正在发送关机指令...");
    }});

    restartButton.addEventListener("click", async () => {{
      await runTimedAction("/api/restart", "确定要在 {{delay}} 秒后重启吗？", "正在发送重启指令...");
    }});

    cancelButton.addEventListener("click", async () => {{
      if (!window.confirm("确定要取消已经安排的关机或重启吗？")) {{
        return;
      }}

      setButtonsDisabled(true);
      statusNode.textContent = "正在发送取消指令...";

      try {{
        const payload = await postJson("/api/cancel-shutdown", {{ token }});
        statusNode.textContent = payload.message || "已取消关机或重启。";
      }} catch (error) {{
        statusNode.textContent = "取消失败：" + error.message;
      }} finally {{
        setButtonsDisabled(false);
      }}
    }});

    sleepButton.addEventListener("click", async () => {{
      if (!window.confirm("确定要让电脑立即休眠吗？")) {{
        return;
      }}

      setButtonsDisabled(true);
      statusNode.textContent = "正在发送休眠指令...";

      try {{
        const payload = await postJson("/api/sleep", {{ token }});
        statusNode.textContent = payload.message || "休眠指令已发送。";
      }} catch (error) {{
        statusNode.textContent = "发送失败：" + error.message;
      }} finally {{
        setButtonsDisabled(false);
      }}
    }});
  </script>
</body>
</html>
"""

    def render_access_denied_page(self) -> str:
        return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>访问被拒绝</title>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #f6f7fb;
      font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
      color: #1f2937;
    }
    .card {
      width: min(100%, 420px);
      background: white;
      border-radius: 20px;
      padding: 28px;
      box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
    }
    h1 { margin-top: 0; }
    p { line-height: 1.7; color: #4b5563; }
  </style>
</head>
<body>
  <div class="card">
    <h1>访问被拒绝</h1>
    <p>这个页面需要使用电脑端生成的完整访问链接。</p>
    <p>请回到主机软件，复制带有 token 的完整地址，或者直接扫描软件界面中的二维码。</p>
  </div>
</body>
</html>
"""

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        service = self

        class RequestHandler(BaseHTTPRequestHandler):
            server_version = "LanShutdownControl/1.2"

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                token = self._extract_query_token(parsed.query)

                if parsed.path == "/":
                    if not service.is_authorized(token):
                        self._send_html(HTTPStatus.FORBIDDEN, service.render_access_denied_page())
                        return
                    self._send_html(HTTPStatus.OK, service.render_control_page())
                    return

                if parsed.path == "/api/status":
                    if not service.is_authorized(token):
                        self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Invalid token."})
                        return
                    self._send_json(HTTPStatus.OK, service.get_status())
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found."})

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                body = self._read_json_body()
                token = str(body.get("token") or self._extract_query_token(parsed.query))

                if not service.is_authorized(token):
                    self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "Invalid token."})
                    return

                if parsed.path == "/api/shutdown":
                    self._handle_shutdown(body)
                    return

                if parsed.path == "/api/restart":
                    self._handle_restart(body)
                    return

                if parsed.path == "/api/cancel-shutdown":
                    self._handle_cancel_shutdown()
                    return

                if parsed.path == "/api/sleep":
                    self._handle_sleep()
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found."})

            def log_message(self, format: str, *args: object) -> None:
                return

            def _handle_shutdown(self, body: dict[str, object]) -> None:
                self._handle_timed_action(
                    body=body,
                    action=service.request_shutdown,
                    success_message_template="关机指令已发送，电脑将在 {delay} 秒后关机。",
                )

            def _handle_restart(self, body: dict[str, object]) -> None:
                self._handle_timed_action(
                    body=body,
                    action=service.request_restart,
                    success_message_template="重启指令已发送，电脑将在 {delay} 秒后重启。",
                )

            def _handle_timed_action(
                self,
                body: dict[str, object],
                action: Callable[[str, int | None], int],
                success_message_template: str,
            ) -> None:
                raw_delay = body.get("delay_seconds")
                try:
                    delay_seconds = None if raw_delay is None else int(raw_delay)
                    actual_delay = action(self.client_address[0], delay_seconds)
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
                    return
                except Exception as exc:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
                    return

                self._send_json(
                    HTTPStatus.ACCEPTED,
                    {
                        "ok": True,
                        "message": success_message_template.format(delay=actual_delay),
                        "delay_seconds": actual_delay,
                    },
                )

            def _handle_cancel_shutdown(self) -> None:
                try:
                    service.request_cancel_shutdown(self.client_address[0])
                except Exception as exc:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
                    return

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "message": "已经发送取消关机 / 重启指令。",
                    },
                )

            def _handle_sleep(self) -> None:
                try:
                    service.request_sleep(self.client_address[0])
                except Exception as exc:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
                    return

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "message": "休眠指令已发送。",
                    },
                )

            def _read_json_body(self) -> dict[str, object]:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0:
                    return {}
                raw = self.rfile.read(content_length)
                if not raw:
                    return {}
                try:
                    return json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    return {}

            @staticmethod
            def _extract_query_token(query: str) -> str:
                return parse_qs(query).get("token", [""])[0]

            def _send_html(self, status: HTTPStatus, body: str) -> None:
                encoded = body.encode("utf-8")
                self.send_response(status.value)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
                encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status.value)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return RequestHandler

    def _normalize_delay(self, delay_seconds: int | None) -> int:
        seconds = self.shutdown_delay_seconds if delay_seconds is None else int(delay_seconds)
        if seconds < 0:
            raise ValueError("delay_seconds must be 0 or greater.")
        return seconds

    def _record_action(self, action_type: str, requester_ip: str, **extra: object) -> dict[str, object]:
        action = {
            "type": action_type,
            "requested_by": requester_ip,
            "requested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        action.update(extra)
        self._last_action = action
        return action
