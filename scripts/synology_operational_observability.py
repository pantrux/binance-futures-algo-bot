#!/usr/bin/env python3
"""Monitorea salud operativa del pipeline Synology vía GitHub Actions.

Genera reporte JSON + resumen Markdown con foco en:
- fallos recientes de gates/workflows,
- degradación de SLO (success rate),
- drift operativo (sin ejecuciones en ventana esperada),
- degradación de health endpoints opcionales.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

DEFAULT_WORKFLOWS = [
    "Synology Release Gate",
    "Synology Smoke Test",
    "Synology Preflight",
    "Synology Artifact Retention",
]


@dataclass
class WorkflowMetrics:
    workflow_name: str
    workflow_id: int | None
    total_runs: int
    success_count: int
    failed_count: int
    cancelled_count: int
    success_rate: float
    latest_conclusion: str | None
    latest_run_at: str | None


@dataclass
class HealthCheckResult:
    name: str
    url: str
    ok: bool
    status_code: int | None
    detail: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_repo(repo: str) -> tuple[str, str]:
    if "/" not in repo:
        raise ValueError(f"Formato de repo inválido: '{repo}', esperado owner/repo")
    owner, name = repo.split("/", 1)
    if not owner or not name:
        raise ValueError(f"Formato de repo inválido: '{repo}', esperado owner/repo")
    return owner, name


def parse_workflows(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


def parse_health_checks(raw_checks: list[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw in raw_checks:
        if "=" in raw:
            name, url = raw.split("=", 1)
            name = name.strip()
            url = url.strip()
        else:
            name = raw.strip()
            url = raw.strip()

        if not name or not url:
            raise ValueError(f"Health check inválido: '{raw}' (usa name=url o URL)")
        parsed.append((name, url))
    return parsed


def github_request(path: str, token: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    base_url = "https://api.github.com"
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"

    req = request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "synology-operational-observability-script",
        },
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def list_workflows(owner: str, repo: str, token: str) -> dict[str, int]:
    payload = github_request(f"/repos/{owner}/{repo}/actions/workflows", token)
    mapping: dict[str, int] = {}
    for wf in payload.get("workflows", []):
        name = wf.get("name")
        wf_id = wf.get("id")
        if isinstance(name, str) and isinstance(wf_id, int):
            mapping[name] = wf_id
    return mapping


def list_completed_runs(owner: str, repo: str, workflow_id: int, token: str, per_page: int = 100) -> list[dict[str, Any]]:
    payload = github_request(
        f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
        token,
        query={"status": "completed", "per_page": per_page},
    )
    runs = payload.get("workflow_runs", [])
    if isinstance(runs, list):
        return runs
    return []


def parse_iso_utc(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_workflow_metrics(
    workflow_name: str,
    workflow_id: int | None,
    runs: list[dict[str, Any]],
    cutoff: datetime,
) -> WorkflowMetrics:
    scoped_runs: list[dict[str, Any]] = []
    for run in runs:
        created_at = parse_iso_utc(run.get("created_at"))
        if created_at and created_at >= cutoff:
            scoped_runs.append(run)

    success_count = 0
    failed_count = 0
    cancelled_count = 0

    for run in scoped_runs:
        conclusion = (run.get("conclusion") or "").lower()
        if conclusion == "success":
            success_count += 1
        elif conclusion in {"failure", "timed_out", "startup_failure", "action_required"}:
            failed_count += 1
        elif conclusion in {"cancelled", "skipped", "neutral", "stale"}:
            cancelled_count += 1
        else:
            cancelled_count += 1

    total_runs = len(scoped_runs)
    success_rate = (success_count / total_runs) if total_runs else 0.0

    latest_run_at = None
    latest_conclusion = None
    if scoped_runs:
        latest = max(scoped_runs, key=lambda r: parse_iso_utc(r.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc))
        latest_run_at = latest.get("created_at")
        latest_conclusion = latest.get("conclusion")

    return WorkflowMetrics(
        workflow_name=workflow_name,
        workflow_id=workflow_id,
        total_runs=total_runs,
        success_count=success_count,
        failed_count=failed_count,
        cancelled_count=cancelled_count,
        success_rate=round(success_rate, 4),
        latest_conclusion=latest_conclusion,
        latest_run_at=latest_run_at,
    )


def run_health_checks(checks: list[tuple[str, str]], timeout_seconds: int) -> list[HealthCheckResult]:
    results: list[HealthCheckResult] = []
    for name, url in checks:
        req = request.Request(url, headers={"User-Agent": "synology-operational-observability-script"})
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                status = response.getcode()
                ok = 200 <= status < 400
                detail = "OK" if ok else f"HTTP {status}"
                results.append(
                    HealthCheckResult(
                        name=name,
                        url=url,
                        ok=ok,
                        status_code=status,
                        detail=detail,
                    )
                )
        except error.HTTPError as exc:
            results.append(
                HealthCheckResult(
                    name=name,
                    url=url,
                    ok=False,
                    status_code=exc.code,
                    detail=f"HTTPError: {exc.code}",
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                HealthCheckResult(
                    name=name,
                    url=url,
                    ok=False,
                    status_code=None,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
    return results


def build_alerts(
    metrics: list[WorkflowMetrics],
    health_results: list[HealthCheckResult],
    min_success_rate: float,
    min_runs: int,
    drift_workflow_names: set[str],
) -> list[str]:
    alerts: list[str] = []

    for metric in metrics:
        if metric.workflow_id is None:
            alerts.append(f"Workflow no encontrado: {metric.workflow_name}")
            continue

        if metric.workflow_name in drift_workflow_names and metric.total_runs < min_runs:
            alerts.append(
                f"Drift operativo: {metric.workflow_name} tiene {metric.total_runs} runs en ventana (mínimo requerido={min_runs})"
            )

        if metric.total_runs > 0 and metric.success_rate < min_success_rate:
            alerts.append(
                f"SLO degradado: {metric.workflow_name} success_rate={metric.success_rate:.2%} (< {min_success_rate:.2%})"
            )

        if metric.latest_conclusion and metric.latest_conclusion.lower() != "success":
            alerts.append(
                f"Fallo reciente: {metric.workflow_name} latest_conclusion={metric.latest_conclusion}"
            )

    for result in health_results:
        if not result.ok:
            alerts.append(f"Health degradado: {result.name} -> {result.detail}")

    return alerts


def render_markdown(
    generated_at: str,
    repo: str,
    window_hours: int,
    min_success_rate: float,
    min_runs: int,
    drift_workflows: list[str],
    metrics: list[WorkflowMetrics],
    health_results: list[HealthCheckResult],
    alerts: list[str],
) -> str:
    lines: list[str] = []
    lines.append("# Synology Operational Observability")
    lines.append("")
    lines.append(f"- Generated at (UTC): `{generated_at}`")
    lines.append(f"- Repo: `{repo}`")
    lines.append(f"- Window: últimas `{window_hours}` horas")
    lines.append(f"- SLO mínimo: `{min_success_rate:.0%}`")
    lines.append(f"- Runs mínimas por workflow en ventana: `{min_runs}`")
    lines.append(f"- Drift aplicado a: `{', '.join(drift_workflows) if drift_workflows else 'ninguno'}`")
    lines.append("")

    lines.append("## Pipeline SLO")
    lines.append("")
    lines.append("| Workflow | Runs | Success | Failed | Cancelled/Other | Success Rate | Latest |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for metric in metrics:
        latest = metric.latest_conclusion or "n/a"
        lines.append(
            f"| {metric.workflow_name} | {metric.total_runs} | {metric.success_count} | {metric.failed_count} | {metric.cancelled_count} | {metric.success_rate:.0%} | {latest} |"
        )

    lines.append("")
    lines.append("## Health checks")
    lines.append("")
    if not health_results:
        lines.append("- Sin health checks configurados")
    else:
        for result in health_results:
            status = "✅" if result.ok else "❌"
            code = result.status_code if result.status_code is not None else "n/a"
            lines.append(f"- {status} `{result.name}` ({result.url}) -> status={code} detail={result.detail}")

    lines.append("")
    lines.append("## Alertas")
    lines.append("")
    if not alerts:
        lines.append("- ✅ Sin alertas")
    else:
        for alert in alerts:
            lines.append(f"- ❌ {alert}")

    lines.append("")
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reporte SLO/alerting para pipeline Synology")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""), help="owner/repo")
    parser.add_argument(
        "--github-token",
        default=os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN", ""),
        help="Token GitHub (GH_TOKEN/GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--workflows",
        default=",".join(DEFAULT_WORKFLOWS),
        help="Lista separada por coma de nombres de workflows",
    )
    parser.add_argument("--window-hours", type=int, default=168, help="Ventana de análisis en horas")
    parser.add_argument("--min-success-rate", type=float, default=0.90, help="SLO mínimo por workflow (0..1)")
    parser.add_argument("--min-runs", type=int, default=1, help="Mínimo de runs por workflow en ventana")
    parser.add_argument(
        "--drift-workflows",
        default="",
        help="Lista separada por coma de workflows a los que se les exige min-runs (vacío => todos)",
    )
    parser.add_argument(
        "--health-check",
        action="append",
        default=[],
        help="Health check opcional en formato name=url (repetible)",
    )
    parser.add_argument("--timeout-seconds", type=int, default=10, help="Timeout HTTP health checks")
    parser.add_argument(
        "--output-json",
        default="artifacts/synology-operational-observability.json",
        help="Ruta de salida JSON",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/synology-operational-observability.md",
        help="Ruta de salida Markdown",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if not args.repo:
            parser.error("--repo es obligatorio (o define GITHUB_REPOSITORY)")
        if not args.github_token:
            parser.error("--github-token es obligatorio (o define GH_TOKEN/GITHUB_TOKEN)")
        if args.window_hours < 1:
            parser.error("--window-hours debe ser >= 1")
        if not (0 < args.min_success_rate <= 1):
            parser.error("--min-success-rate debe estar en (0,1]")
        if args.min_runs < 1:
            parser.error("--min-runs debe ser >= 1")

        owner, repo = parse_repo(args.repo)
        workflows = parse_workflows(args.workflows)
        if not workflows:
            parser.error("--workflows no puede estar vacío")
        drift_workflows = parse_workflows(args.drift_workflows) if args.drift_workflows else workflows
        health_checks = parse_health_checks(args.health_check)

        cutoff = utc_now() - timedelta(hours=args.window_hours)
        known_workflows = list_workflows(owner, repo, args.github_token)

        metrics: list[WorkflowMetrics] = []
        for wf_name in workflows:
            wf_id = known_workflows.get(wf_name)
            runs: list[dict[str, Any]] = []
            if wf_id is not None:
                runs = list_completed_runs(owner, repo, wf_id, args.github_token)
            metrics.append(compute_workflow_metrics(wf_name, wf_id, runs, cutoff))

        health_results = run_health_checks(health_checks, timeout_seconds=args.timeout_seconds)
        alerts = build_alerts(
            metrics=metrics,
            health_results=health_results,
            min_success_rate=args.min_success_rate,
            min_runs=args.min_runs,
            drift_workflow_names=set(drift_workflows),
        )

        generated_at = utc_now().isoformat()
        payload = {
            "generated_at": generated_at,
            "repo": args.repo,
            "window_hours": args.window_hours,
            "min_success_rate": args.min_success_rate,
            "min_runs": args.min_runs,
            "drift_workflows": drift_workflows,
            "workflows": [asdict(item) for item in metrics],
            "health_checks": [asdict(item) for item in health_results],
            "alerts": alerts,
            "alert_count": len(alerts),
            "overall_status": "ALERT" if alerts else "OK",
        }

        output_json = Path(args.output_json)
        output_md = Path(args.output_md)

        write_text(output_json, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        markdown = render_markdown(
            generated_at=generated_at,
            repo=args.repo,
            window_hours=args.window_hours,
            min_success_rate=args.min_success_rate,
            min_runs=args.min_runs,
            drift_workflows=drift_workflows,
            metrics=metrics,
            health_results=health_results,
            alerts=alerts,
        )
        write_text(output_md, markdown)

        print(f"overall_status={payload['overall_status']}")
        print(f"alert_count={payload['alert_count']}")
        print(f"output_json={output_json}")
        print(f"output_md={output_md}")

        return 1 if alerts else 0
    except error.HTTPError as exc:
        print(f"GitHub API HTTPError: {exc.code} {exc.reason}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error inesperado: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
