#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STEP_PATTERN = re.compile(r"^##\s+(.+?):\s+(PASS|FAIL)\s*$")
RESULT_PATTERN = re.compile(r"^\*\*(PASS|FAIL)\*\*\s*$")


def parse_report(text: str) -> dict:
    steps: list[dict[str, str]] = []
    overall = "UNKNOWN"

    for line in text.splitlines():
        step_match = STEP_PATTERN.match(line.strip())
        if step_match:
            steps.append({"name": step_match.group(1), "status": step_match.group(2)})
            continue

        result_match = RESULT_PATTERN.match(line.strip())
        if result_match:
            overall = result_match.group(1)

    return {
        "overall": overall,
        "steps": steps,
        "step_count": len(steps),
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
