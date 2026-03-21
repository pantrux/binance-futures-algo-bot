from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "synology_shadow_run_gate.py"
SPEC = importlib.util.spec_from_file_location("synology_shadow_run_gate", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_fetch_shadow_run_summary_includes_timeframe_query_and_metrics_header(monkeypatch):
    captured: dict[str, object] = {}

    def fake_fetch_json(url: str, *, headers=None, timeout=40):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {"ok": True}

    monkeypatch.setattr(MODULE, "fetch_json", fake_fetch_json)

    payload = MODULE.fetch_shadow_run_summary("https://api.example.com/", "secret-key", 30, "1h")

    assert payload == {"ok": True}
    assert captured["url"] == "https://api.example.com/reporting/shadow-run-summary?window_days=30&timeframe=1h"
    assert captured["headers"] == {"x-metrics-key": "secret-key"}



def test_fetch_command_center_snapshot_forwards_metrics_header(monkeypatch):
    captured: dict[str, object] = {}

    def fake_fetch_json(url: str, *, headers=None, timeout=40):
        captured["url"] = url
        captured["headers"] = headers
        return {
            "generated_at": "2026-03-21T00:00:00Z",
            "summary": {"trade_plans_total": 2, "open_positions": 1, "risk_events_total": 0},
            "shadow_run": {"compared_pairs": 1, "shadow_run_duration_days": 7},
            "operation_snapshots": [],
            "timeline": [],
        }

    monkeypatch.setattr(MODULE, "fetch_json", fake_fetch_json)

    payload = MODULE.fetch_command_center_snapshot("https://api.example.com/", metrics_api_key="secret-key")

    assert payload["summary"]["trade_plans_total"] == 2
    assert captured["url"] == "https://api.example.com/dashboard/command-center"
    assert captured["headers"] == {"x-metrics-key": "secret-key"}



def test_to_markdown_includes_timeframe_line():
    summary = {
        "window_days": 30,
        "timeframe": "15m",
        "shadow_run_duration_days": 8,
        "paper_executed_trade_plans": 210,
        "testnet_executed_trade_plans": 205,
        "compared_pairs": 200,
        "unmatched_paper": 5,
        "unmatched_testnet": 4,
        "testnet_fill_rate_pct": 99.0,
        "avg_testnet_slippage_bps": 0.8,
        "critical_risk_events_7d": 0,
        "warning_risk_events_7d": 1,
        "avg_risk_events_per_day_30d": 0.3,
        "symbols": [],
    }
    evaluation = {"overall": "PASS", "steps": []}
    command_center = {
        "generated_at": "2026-03-21T00:00:00Z",
        "operation_snapshots_visible": 0,
        "timeline_events_visible": 0,
        "summary": {"trade_plans_total": 2, "open_positions": 1, "risk_events_total": 0},
        "top_operations": [],
    }

    markdown = MODULE.to_markdown(summary, evaluation, command_center)

    assert "- Timeframe: **15m**" in markdown



def test_main_passes_timeframe_to_summary_fetch_and_metrics_to_command_center(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_fetch_shadow_run_summary(api_base_url, metrics_api_key, window_days, timeframe):
        captured["summary_args"] = (api_base_url, metrics_api_key, window_days, timeframe)
        return {
            "window_days": window_days,
            "timeframe": timeframe,
            "shadow_run_duration_days": 8,
            "paper_executed_trade_plans": 220,
            "testnet_executed_trade_plans": 215,
            "compared_pairs": 210,
            "unmatched_paper": 3,
            "unmatched_testnet": 2,
            "testnet_fill_rate_pct": 99.0,
            "avg_testnet_slippage_bps": 0.5,
            "critical_risk_events_7d": 0,
            "warning_risk_events_7d": 1,
            "avg_risk_events_per_day_30d": 0.5,
            "symbols": [],
        }

    def fake_fetch_command_center_snapshot(api_base_url, *, metrics_api_key=None, limit=3):
        captured["command_center_args"] = (api_base_url, metrics_api_key, limit)
        return {
            "generated_at": "2026-03-21T00:00:00Z",
            "operation_snapshots_visible": 0,
            "timeline_events_visible": 0,
            "summary": {"trade_plans_total": 10, "open_positions": 2, "risk_events_total": 1},
            "top_operations": [],
        }

    monkeypatch.setattr(MODULE, "fetch_shadow_run_summary", fake_fetch_shadow_run_summary)
    monkeypatch.setattr(MODULE, "fetch_command_center_snapshot", fake_fetch_command_center_snapshot)

    output_json = tmp_path / "gate.json"
    output_md = tmp_path / "gate.md"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "synology_shadow_run_gate.py",
            "--api-base-url",
            "https://api.example.com",
            "--metrics-api-key",
            "secret-key",
            "--window-days",
            "14",
            "--timeframe",
            "1h",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )

    exit_code = MODULE.main()

    assert exit_code == 0
    assert captured["summary_args"] == ("https://api.example.com", "secret-key", 14, "1h")
    assert captured["command_center_args"] == ("https://api.example.com", "secret-key", 3)
    assert output_json.exists()
    assert output_md.exists()
