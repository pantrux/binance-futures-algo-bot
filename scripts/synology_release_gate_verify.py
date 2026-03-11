#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_OVERALL = {"PASS", "FAIL"}


def error(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def verify_payload(payload: object, expected_steps: list[str]) -> int:
    if not isinstance(payload, dict):
        return error("payload root debe ser objeto JSON")

    missing = [key for key in ("overall", "steps", "step_count") if key not in payload]
    if missing:
        return error(f"faltan campos requeridos: {', '.join(missing)}")

    overall = payload.get("overall")
    if overall not in ALLOWED_OVERALL:
        return error(f"overall inválido: {overall}")

    steps = payload.get("steps")
    if not isinstance(steps, list):
        return error("steps debe ser lista")

    step_count = payload.get("step_count")
    if not isinstance(step_count, int) or isinstance(step_count, bool):
        return error("step_count debe ser entero")

    if step_count != len(steps):
        return error(f"step_count inconsistente: {step_count} != {len(steps)}")

    names: list[str] = []
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            return error(f"steps[{idx}] debe ser objeto")
        if step.get("status") not in {"PASS", "FAIL"}:
            return error(f"steps[{idx}].status inválido: {step.get('status')}")
        name = step.get("name")
        if not isinstance(name, str) or not name.strip():
            return error(f"steps[{idx}].name inválido")
        names.append(name)

    if expected_steps:
        if names != expected_steps:
            return error(f"steps esperados {expected_steps}, recibidos {names}")

    print("JSON summary verification: PASS")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: synology_release_gate_verify.py <summary.json> [expected_steps_csv]", file=sys.stderr)
        return 2

    json_path = Path(sys.argv[1])
    expected_steps_csv = sys.argv[2] if len(sys.argv) > 2 else "Preflight,Smoke"
    expected_steps = [item.strip() for item in expected_steps_csv.split(",") if item.strip()]

    if not json_path.exists():
        return error(f"summary JSON no encontrado: {json_path}")

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return error(f"JSON inválido: {exc}")

    return verify_payload(payload, expected_steps)


if __name__ == "__main__":
    raise SystemExit(main())
