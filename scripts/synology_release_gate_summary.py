#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STEP_PATTERN = re.compile(r"^##\s+(.+?):\s+(PASS|FAIL)\s*$")
RESULT_PATTERN = re.compile(r"^\*\*(PASS|FAIL)\*\*\s*$")
HEADER_ITEM_PATTERN = re.compile(r"^- ([A-Za-z_][A-Za-z0-9_ ()/-]*?):\s*(.+?)\s*$")
WARNING_PATTERN = re.compile(r"^(?:⚠️|Warning:)\s*(.+?)\s*$")


def parse_report(text: str) -> dict:
    steps: list[dict[str, str]] = []
    overall = "UNKNOWN"
    generated_at_utc: str | None = None
    inputs_used: dict[str, str] = {}
    warnings: list[str] = []
    in_fence = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        header_item_match = HEADER_ITEM_PATTERN.match(stripped)
        if header_item_match:
            key = header_item_match.group(1)
            value = header_item_match.group(2)
            if key == "Generated at (UTC)":
                generated_at_utc = value
            else:
                inputs_used[key] = value
            continue

        warning_match = WARNING_PATTERN.match(stripped)
        if warning_match:
            warnings.append(warning_match.group(1))
            continue

        step_match = STEP_PATTERN.match(stripped)
        if step_match:
            steps.append({"name": step_match.group(1), "status": step_match.group(2)})
            continue

        result_match = RESULT_PATTERN.match(stripped)
        if result_match:
            overall = result_match.group(1)

    if in_fence:
        print("Warning: unclosed code fence detected in report; results may be incomplete.", file=sys.stderr)

    first_failing_step = next((step for step in steps if step["status"] == "FAIL"), None)

    return {
        "overall": overall,
        "steps": steps,
        "step_count": len(steps),
        "generated_at_utc": generated_at_utc,
        "inputs_used": inputs_used,
        "warnings": warnings,
        "first_failing_step": first_failing_step,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: synology_release_gate_summary.py <report.md> [output.json]", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("artifacts/synology-release-gate.json")

    if not report_path.exists():
        print(f"Report not found: {report_path}", file=sys.stderr)
        return 1

    parsed = parse_report(report_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(parsed, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
