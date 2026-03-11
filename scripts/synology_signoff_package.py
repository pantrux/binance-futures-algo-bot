#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root debe ser objeto")
    for key in ("overall", "steps", "step_count"):
        if key not in data:
            raise ValueError(f"JSON sin campo requerido: {key}")
    return data


def main() -> int:
    gate_md = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/synology-release-gate.md")
    gate_json = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("artifacts/synology-release-gate.json")
    checklist_md = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("artifacts/synology-release-checklist.md")
    output_md = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("artifacts/synology-signoff-package.md")

    for p in (gate_md, gate_json, checklist_md):
        if not p.exists():
            print(f"Missing required file: {p}", file=sys.stderr)
            return 1

    try:
        summary = load_json(gate_json)
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid gate JSON: {exc}", file=sys.stderr)
        return 1

    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    output_md.parent.mkdir(parents=True, exist_ok=True)

    steps_lines = []
    for step in summary.get("steps", []):
        name = step.get("name", "unknown")
        status = step.get("status", "unknown")
        steps_lines.append(f"- {name}: {status}")

    content = f"""# Synology Sign-off Package

- Generated: {generated_at}
- Gate markdown: `{gate_md}`
- Gate json: `{gate_json}`
- Checklist: `{checklist_md}`

## Gate summary
- overall: **{summary.get('overall')}**
- step_count: **{summary.get('step_count')}**

{chr(10).join(steps_lines)}

## Checklist status
- Archivo de checklist presente: ✅
- Archivo de gate markdown presente: ✅
- Archivo de gate json presente: ✅

## Referencias
- `{gate_md}`
- `{gate_json}`
- `{checklist_md}`
"""

    output_md.write_text(content, encoding="utf-8")
    print(str(output_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
