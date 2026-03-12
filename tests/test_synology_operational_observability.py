import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_operational_observability.py"
    spec = importlib.util.spec_from_file_location("synology_operational_observability", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def obs_module():
    return load_module()


def test_parse_health_checks_supports_name_url_and_raw_url(obs_module):
    checks = obs_module.parse_health_checks([
        "api=https://example.com/api/health",
        "https://example.com/web/health",
    ])
    assert checks == [
        ("api", "https://example.com/api/health"),
        ("https://example.com/web/health", "https://example.com/web/health"),
    ]


def test_parse_health_checks_rejects_invalid_entry(obs_module):
    with pytest.raises(ValueError):
        obs_module.parse_health_checks(["="])


def test_compute_workflow_metrics_counts_by_conclusion(obs_module):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    runs = [
        {"created_at": now_iso, "conclusion": "success"},
        {"created_at": now_iso, "conclusion": "failure"},
        {"created_at": now_iso, "conclusion": "cancelled"},
    ]

    metrics = obs_module.compute_workflow_metrics(
        workflow_name="Synology Release Gate",
        workflow_id=123,
        runs=runs,
        cutoff=cutoff,
    )

    assert metrics.total_runs == 3
    assert metrics.success_count == 1
    assert metrics.failed_count == 1
    assert metrics.cancelled_count == 1
    assert metrics.success_rate == pytest.approx(1 / 3, abs=1e-4)


def test_build_alerts_detects_missing_workflow_and_health_failure(obs_module):
    missing_workflow = obs_module.WorkflowMetrics(
        workflow_name="Missing Workflow",
        workflow_id=None,
        total_runs=0,
        success_count=0,
        failed_count=0,
        cancelled_count=0,
        success_rate=0.0,
        latest_conclusion=None,
        latest_run_at=None,
    )
    unhealthy = obs_module.HealthCheckResult(
        name="api",
        url="https://example.com/health",
        ok=False,
        status_code=503,
        detail="HTTP 503",
    )

    alerts = obs_module.build_alerts(
        metrics=[missing_workflow],
        health_results=[unhealthy],
        min_success_rate=0.9,
        min_runs=1,
        drift_workflow_names={"Missing Workflow"},
    )

    assert any("Workflow no encontrado" in alert for alert in alerts)
    assert any("Health degradado" in alert for alert in alerts)


def test_render_markdown_includes_pipeline_and_alerts(obs_module):
    metric = obs_module.WorkflowMetrics(
        workflow_name="Synology Smoke Test",
        workflow_id=111,
        total_runs=2,
        success_count=1,
        failed_count=1,
        cancelled_count=0,
        success_rate=0.5,
        latest_conclusion="failure",
        latest_run_at="2026-03-12T00:00:00Z",
    )

    output = obs_module.render_markdown(
        generated_at="2026-03-12T00:01:00Z",
        repo="pantrux/binance-futures-algo-bot",
        window_hours=24,
        min_success_rate=0.9,
        min_runs=1,
        drift_workflows=["Synology Smoke Test"],
        metrics=[metric],
        health_results=[],
        alerts=["SLO degradado: Synology Smoke Test"],
    )

    assert "# Synology Operational Observability" in output
    assert "Synology Smoke Test" in output
    assert "SLO degradado" in output
