from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "synology_smoke_test.sh"


class FixtureServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], payload: dict[str, Any], html: str):
        self.payload = payload
        self.html = html
        super().__init__(server_address, FixtureHandler)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/dashboard/summary":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/trade-plans":
            self._send_json(200, [])
            return
        if self.path == "/dashboard/command-center":
            self._send_json(200, self.server.payload)
            return
        if self.path == "/integrations/binance/testnet/ping":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/metrics":
            self._send_text(200, "metric_a 1\n")
            return
        if self.path == "/":
            self._send_html(200, self.server.html)
            return

        self._send_text(404, "not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _send_json(self, status: int, body: Any) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, status: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_fixture_server(payload: dict[str, Any], html: str):
    server = FixtureServer(("127.0.0.1", 0), payload=payload, html=html)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{port}"


def build_payload(*, latest_risk_context: dict[str, Any] | None, recent_risk_events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "operation_snapshots": [
            {
                "order_history": [],
                "position_history": [],
                "risk_event_history": [],
                "timeline_history": [],
                "reconciliation_recommended_actions": [],
                "latest_risk_context": latest_risk_context,
            }
        ],
        "recent_risk_events": recent_risk_events,
    }


def build_html(*, include_context_markers: bool) -> str:
    markers = "<div class='context-list'><span class='context-chip'>BTCUSDT</span></div>" if include_context_markers else ""
    return (
        "<html><body>"
        "bot "
        "Detalle por trade plan "
        "Historial de órdenes "
        "Historial de posiciones "
        "Historial de riesgo "
        "Reconcile actual "
        f"{markers}"
        "</body></html>"
    )


def run_smoke(base_url: str) -> subprocess.CompletedProcess[str]:
    python_dir = str(Path(sys.executable).resolve().parent)
    env = {
        "PATH": os.pathsep.join([python_dir, os.environ.get("PATH", "/usr/bin:/bin")]),
        "API_BASE_URL": base_url,
        "WEB_BASE_URL": base_url,
        "STRICT_EXTERNAL_CHECKS": "false",
    }
    return subprocess.run(
        ["bash", str(SMOKE_SCRIPT)],
        cwd="/tmp",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_synology_smoke_script_passes_with_non_empty_context_and_markers() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True))
    try:
        result = run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr + result.stdout
    assert "HAS_NON_EMPTY_CONTEXT=1" in result.stdout
    assert "context-list" in result.stdout
    assert "context-chip" in result.stdout


def test_synology_smoke_script_passes_with_clean_payload_without_markers() -> None:
    payload = build_payload(
        latest_risk_context={},
        recent_risk_events=[{"context": {}}],
    )
    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=False))
    try:
        result = run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr + result.stdout
    assert "HAS_NON_EMPTY_CONTEXT=0" in result.stdout
    assert "Se omiten marcadores context-list/context-chip" in result.stdout


def test_synology_smoke_script_fails_when_context_is_present_but_html_markers_are_missing() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=False))
    try:
        result = run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode != 0
    assert "no contiene 'context-list'" in result.stderr
