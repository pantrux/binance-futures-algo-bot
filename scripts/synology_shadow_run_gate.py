#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import parse, request


def fetch_shadow_run_summary(api_base_url: str, metrics_api_key: str, window_days: int) -> dict:
    query = parse.urlencode({"window_days": window_days})
    req = request.Request(
        f"{api_base_url.rstrip('/')}/reporting/shadow-run-summary?{query}",
        headers={"x-metrics-key": metrics_api_key},
    )
    with request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def evaluate(summary: dict, args: argparse.Namespace) -> dict:
    steps = []

    def add_step(name: str, ok: bool, detail: str) -> None:
        steps.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    add_step(
        "Duración shadow run",
        summary["shadow_run_duration_days"] >= args.min_shadow_days,
        f"duration_days={summary['shadow_run_duration_days']} min_required={args.min_shadow_days}",
    )
    add_step(
        "Volumen paper",
        summary["paper_executed_trade_plans"] >= args.min_trades,
        f"paper_executed={summary['paper_executed_trade_plans']} min_required={args.min_trades}",
    )
    add_step(
        "Volumen testnet",
        summary["testnet_executed_trade_plans"] >= args.min_trades,
        f"testnet_executed={summary['testnet_executed_trade_plans']} min_required={args.min_trades}",
    )
    add_step(
        "Pares comparados",
        summary["compared_pairs"] >= args.min_trades,
        f"compared_pairs={summary['compared_pairs']} min_required={args.min_trades}",
    )

    fill_rate = summary.get("testnet_fill_rate_pct")
    add_step(
        "Fill rate testnet",
        fill_rate is not None and fill_rate >= args.min_fill_rate_pct,
        f"fill_rate_pct={fill_rate} min_required={args.min_fill_rate_pct}",
    )

    avg_slippage_bps = summary.get("avg_testnet_slippage_bps")
    add_step(
        "Slippage promedio testnet",
        avg_slippage_bps is not None and avg_slippage_bps <= args.max_avg_slippage_bps,
        f"avg_slippage_bps={avg_slippage_bps} max_allowed={args.max_avg_slippage_bps}",
    )

    risk_ok = (
        summary["critical_risk_events_7d"] <= args.max_critical_risk_events_7d
        and summary["warning_risk_events_7d"] <= args.max_warning_risk_events_7d
        and summary["avg_risk_events_per_day_30d"] <= args.max_avg_risk_events_per_day_30d
    )
    add_step(
        "Incidentes operativos",
        risk_ok,
        (
            "critical_7d={critical} max_critical={max_critical}; warning_7d={warning} max_warning={max_warning}; "
            "avg_risk_events_per_day_30d={avg_30d} max_avg_30d={max_avg_30d}"
        ).format(
            critical=summary["critical_risk_events_7d"],
            max_critical=args.max_critical_risk_events_7d,
            warning=summary["warning_risk_events_7d"],
            max_warning=args.max_warning_risk_events_7d,
            avg_30d=summary["avg_risk_events_per_day_30d"],
            max_avg_30d=args.max_avg_risk_events_per_day_30d,
        ),
    )

    overall = "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL"
    return {"overall": overall, "steps": steps}


def to_markdown(summary: dict, evaluation: dict) -> str:
    lines = [
        "# Shadow Run Gate",
        "",
        f"**{evaluation['overall']}**",
        "",
        f"- Ventana analizada: **{summary['window_days']} días**",
        f"- Duración observada: **{summary['shadow_run_duration_days']} días**",
        f"- Paper ejecutado: **{summary['paper_executed_trade_plans']}**",
        f"- Testnet ejecutado: **{summary['testnet_executed_trade_plans']}**",
        f"- Pares comparados: **{summary['compared_pairs']}**",
        f"- Unmatched paper/testnet: **{summary['unmatched_paper']} / {summary['unmatched_testnet']}**",
        f"- Fill rate testnet: **{summary['testnet_fill_rate_pct']}**",
        f"- Slippage promedio (bps): **{summary['avg_testnet_slippage_bps']}**",
        f"- Risk events 7d (critical/warning): **{summary['critical_risk_events_7d']} / {summary['warning_risk_events_7d']}**",
        f"- Risk events promedio por día 30d: **{summary['avg_risk_events_per_day_30d']}**",
        "",
    ]

    for step in evaluation["steps"]:
        lines.extend(
            [
                f"## {step['name']}: {step['status']}",
                "",
                f"- {step['detail']}",
                "",
            ]
        )

    if summary.get("symbols"):
        lines.extend(["## Desglose por símbolo", ""])
        for item in summary["symbols"]:
            lines.append(
                "- {symbol}: paper={paper}, testnet={testnet}, pairs={pairs}, unmatched={unmatched_paper}/{unmatched_testnet}, "
                "entry_diff={entry}, risk_diff={risk}, notional_diff={notional}".format(
                    symbol=item["symbol"],
                    paper=item["paper_executed_trade_plans"],
                    testnet=item["testnet_executed_trade_plans"],
                    pairs=item["compared_pairs"],
                    unmatched_paper=item["unmatched_paper"],
                    unmatched_testnet=item["unmatched_testnet"],
                    entry=item["avg_entry_price_diff_pct"],
                    risk=item["avg_applied_risk_diff_pct"],
                    notional=item["avg_max_notional_diff_pct"],
                )
            )
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evalúa el Gate C de shadow run en Synology")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--metrics-api-key", required=True)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--min-shadow-days", type=float, default=7)
    parser.add_argument("--min-trades", type=int, default=200)
    parser.add_argument("--min-fill-rate-pct", type=float, default=98)
    parser.add_argument("--max-avg-slippage-bps", type=float, default=1)
    parser.add_argument("--max-critical-risk-events-7d", type=int, default=0)
    parser.add_argument("--max-warning-risk-events-7d", type=int, default=3)
    parser.add_argument("--max-avg-risk-events-per-day-30d", type=float, default=1)
    parser.add_argument("--output-json", default="artifacts/synology-shadow-run-gate.json")
    parser.add_argument("--output-md", default="artifacts/synology-shadow-run-gate.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = fetch_shadow_run_summary(args.api_base_url, args.metrics_api_key, args.window_days)
    evaluation = evaluate(summary, args)
    payload = {"summary": summary, "evaluation": evaluation}

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(to_markdown(summary, evaluation) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False))
    return 0 if evaluation["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
