import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class IntegrationHandler(BaseHTTPRequestHandler):
    api_requests: list[dict[str, Any]] = []
    authorization_headers: list[str | None] = []

    def do_GET(self) -> None:
        if self.path != "/article":
            self.send_error(404)
            return
        body = (
            "<html><head><title>端到端测试文章</title></head>"
            "<body><article>"
            + "这是供真实 CLI 进程读取的正文，包含数字 118 和必要限定条件。" * 20
            + "</article></body></html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/chat/completions":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size))
        self.api_requests.append(request)
        self.authorization_headers.append(self.headers.get("Authorization"))
        if request.get("stream"):
            body = (
                'data: {"choices":[{"delta":{"content":"# 流式结果\\n\\n"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"端到端流式成功。"}}]}\n\n'
                'data: {"choices":[],"usage":{"total_tokens":88}}\n\n'
                "data: [DONE]\n\n"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "# 核心结果\n\n数字是 118，且保留限定条件。"
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
            },
            ensure_ascii=False,
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def _run_cli(
    server: ThreadingHTTPServer, *arguments: str
) -> subprocess.CompletedProcess[str]:
    port = server.server_address[1]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "FANTREAD_FRESH": "1",
            "DEEPSEEK_API_KEY": "integration-key",
            "DEEPSEEK_BASE_URL": f"http://127.0.0.1:{port}",
            "NO_PROXY": "127.0.0.1,localhost",
        }
    )
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        environment.pop(name, None)
    return subprocess.run(
        [sys.executable, "-m", "fantread", *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_real_cli_process_fetches_prompts_and_outputs_json() -> None:
    IntegrationHandler.api_requests = []
    IntegrationHandler.authorization_headers = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), IntegrationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        completed = _run_cli(
            server,
            f"http://127.0.0.1:{port}/article",
            "只关注数字和限定条件。",
            "--format",
            "json",
            "--no-stream",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["title"] == "端到端测试文章"
    assert result["model"] == "deepseek-v4-flash"
    assert result["usage"]["total_tokens"] == 120
    assert result["content"].startswith("# 核心结果")
    assert "只关注数字和限定条件。" not in result["content"]

    assert len(IntegrationHandler.api_requests) == 1
    api_request = IntegrationHandler.api_requests[0]
    assert api_request["model"] == "deepseek-v4-flash"
    assert api_request["stream"] is False
    assert api_request["thinking"] == {"type": "disabled"}
    assert "只关注数字和限定条件。" in api_request["messages"][1]["content"]
    assert IntegrationHandler.authorization_headers == ["Bearer integration-key"]


def test_real_cli_process_reports_page_error_before_requesting_key() -> None:
    IntegrationHandler.api_requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), IntegrationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        completed = _run_cli(
            server,
            f"http://127.0.0.1:{port}/missing",
            "--format",
            "json",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert completed.returncode == 1
    assert "页面返回 HTTP 404" in completed.stderr
    assert IntegrationHandler.api_requests == []


def test_real_cli_process_handles_streaming_text_output() -> None:
    IntegrationHandler.api_requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), IntegrationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        completed = _run_cli(
            server,
            f"http://127.0.0.1:{port}/article",
            "--format",
            "text",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert completed.returncode == 0, completed.stderr
    assert "流式结果" in completed.stdout
    assert "端到端流式成功。" in completed.stdout
    assert IntegrationHandler.api_requests[0]["stream"] is True
