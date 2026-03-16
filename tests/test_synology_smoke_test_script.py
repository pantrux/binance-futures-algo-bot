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
    def __init__(
        self,
        server_address: tuple[str, int],
        payload: dict[str, Any],
        html: str,
        overrides: dict[str, tuple[int, Any, str]] | None = None,
        metrics_api_key: str | None = None,
    ):
        self.payload = payload
        self.html = html
        self.overrides = overrides or {}
        self.metrics_api_key = metrics_api_key
        super().__init__(server_address, FixtureHandler)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        override = self.server.overrides.get(self.path)
        if override is not None:
            status, body, content_type = override
            if content_type == "application/json":
                self._send_json(status, body)
            elif content_type == "text/html":
                self._send_html(status, str(body))
            else:
                self._send_text(status, str(body))
            return

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
            expected_metrics_key = self.server.metrics_api_key
            if expected_metrics_key is not None:
                provided_key = self.headers.get("x-metrics-key")
                if provided_key != expected_metrics_key:
                    self._send_text(403, "forbidden")
                    return
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


def run_fixture_server(
    payload: dict[str, Any],
    html: str,
    overrides: dict[str, tuple[int, Any, str]] | None = None,
    metrics_api_key: str | None = None,
) -> tuple[FixtureServer, threading.Thread, str]:
    server = FixtureServer(
        ("127.0.0.1", 0),
        payload=payload,
        html=html,
        overrides=overrides,
        metrics_api_key=metrics_api_key,
    )
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{port}"


def stop_fixture_server(server: FixtureServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
    if thread.is_alive():
        raise RuntimeError("fixture thread sigue vivo tras shutdown()")


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


def run_smoke(
    base_url: str,
    *,
    metrics_api_key: str | None = None,
    strict_external_checks: bool = False,
) -> subprocess.CompletedProcess[str]:
    python_dir = str(Path(sys.executable).resolve().parent)
    env = {
        "PATH": os.pathsep.join([python_dir, os.environ.get("PATH", "/usr/bin:/bin")]),
        "API_BASE_URL": base_url,
        "WEB_BASE_URL": base_url,
        "STRICT_EXTERNAL_CHECKS": "true" if strict_external_checks else "false",
    }
    if metrics_api_key is not None:
        env["METRICS_API_KEY"] = metrics_api_key
    return subprocess.run(
        ["bash", str(SMOKE_SCRIPT)],
        cwd="/tmp",
        text=True,
        capture_output=True,
        env=env,
        check=False,
        timeout=120,
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
        stop_fixture_server(server, thread)

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
        stop_fixture_server(server, thread)

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
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "no contiene 'context-list'" in result.stderr


def test_synology_smoke_script_fails_when_command_center_payload_is_invalid() -> None:
    invalid_payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[{"message": "missing-context"}],
    )

    server, thread, base_url = run_fixture_server(invalid_payload, build_html(include_context_markers=True))
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "recent_risk_events[*] no expone context" in result.stderr


def test_synology_smoke_script_fails_when_health_endpoint_returns_unexpected_status() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/health": (503, {"status": "down"}, "application/json"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /health no cumple" in result.stderr


def test_synology_smoke_script_fails_when_metrics_returns_unexpected_status_without_auth() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/metrics": (500, "boom", "text/plain"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /metrics respondió estado inesperado (500) sin METRICS_API_KEY" in result.stderr


def test_synology_smoke_script_fails_when_dashboard_summary_returns_unexpected_status() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/dashboard/summary": (502, {"status": "bad-gateway"}, "application/json"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /dashboard/summary no cumple" in result.stderr


def test_synology_smoke_script_fails_when_trade_plans_returns_unexpected_status() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/trade-plans": (503, {"status": "degraded"}, "application/json"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /trade-plans no cumple" in result.stderr


def test_synology_smoke_script_fails_when_web_root_returns_unexpected_status() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/": (503, "web down", "text/html"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB / respondió HTTP 503 (esperado 200)" in result.stderr


def test_synology_smoke_script_fails_when_web_root_body_is_empty() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/": (200, "", "text/html"),
    }

    server, thread, base_url = run_fixture_server(payload, build_html(include_context_markers=True), overrides=overrides)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB / sin respuesta desde" in result.stderr


def test_synology_smoke_script_fails_when_web_root_is_missing_bot_marker() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    html = build_html(include_context_markers=True).replace("bot ", "")

    server, thread, base_url = run_fixture_server(payload, html)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB / no contiene 'bot'" in result.stderr


def test_synology_smoke_script_fails_when_web_root_is_missing_command_center_marker() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    html = build_html(include_context_markers=True).replace("Historial de riesgo ", "")

    server, thread, base_url = run_fixture_server(payload, html)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB command center no contiene 'Historial de riesgo'" in result.stderr


def test_synology_smoke_script_fails_when_web_root_is_missing_trade_plan_marker() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    html = build_html(include_context_markers=True).replace("Detalle por trade plan ", "")

    server, thread, base_url = run_fixture_server(payload, html)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB command center no contiene 'Detalle por trade plan'" in result.stderr


def test_synology_smoke_script_fails_when_web_root_is_missing_reconcile_marker() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    html = build_html(include_context_markers=True).replace("Reconcile actual ", "")

    server, thread, base_url = run_fixture_server(payload, html)
    try:
        result = run_smoke(base_url)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "WEB command center no contiene 'Reconcile actual'" in result.stderr


def test_synology_smoke_script_passes_when_metrics_returns_200_with_expected_auth() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )

    server, thread, base_url = run_fixture_server(
        payload,
        build_html(include_context_markers=True),
        metrics_api_key="secret-metrics-key",
    )
    try:
        result = run_smoke(base_url, metrics_api_key="secret-metrics-key")
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode == 0, result.stderr + result.stdout
    assert "API /metrics (auth) (200)" in result.stdout


def test_synology_smoke_script_fails_when_metrics_auth_is_incorrect() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )

    server, thread, base_url = run_fixture_server(
        payload,
        build_html(include_context_markers=True),
        metrics_api_key="secret-metrics-key",
    )
    try:
        result = run_smoke(base_url, metrics_api_key="wrong-key")
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /metrics (auth) no cumple (esperado 200)" in result.stderr


def test_synology_smoke_script_passes_when_testnet_ping_fails_with_strict_external_checks_disabled() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/integrations/binance/testnet/ping": (503, {"status": "down"}, "application/json"),
    }

    server, thread, base_url = run_fixture_server(
        payload,
        build_html(include_context_markers=True),
        overrides=overrides,
    )
    try:
        result = run_smoke(base_url, strict_external_checks=False)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Se omite fallo de testnet/ping por STRICT_EXTERNAL_CHECKS=false" in result.stdout


def test_synology_smoke_script_fails_when_testnet_ping_fails_with_strict_external_checks_enabled() -> None:
    payload = build_payload(
        latest_risk_context={"symbol": "BTCUSDT"},
        recent_risk_events=[],
    )
    overrides = {
        "/integrations/binance/testnet/ping": (503, {"status": "down"}, "application/json"),
    }

    server, thread, base_url = run_fixture_server(
        payload,
        build_html(include_context_markers=True),
        overrides=overrides,
    )
    try:
        result = run_smoke(base_url, strict_external_checks=True)
    finally:
        stop_fixture_server(server, thread)

    assert result.returncode != 0
    assert "API /integrations/binance/testnet/ping no cumple" in result.stderr
