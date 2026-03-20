#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_OVERALL = {"PASS", "FAIL"}
ALLOWED_STEP_STATUS = {"PASS", "FAIL"}


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
    parsed_steps: list[dict[str, str]] = []
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            return error(f"steps[{idx}] debe ser objeto")
        if step.get("status") not in ALLOWED_STEP_STATUS:
            return error(f"steps[{idx}].status inválido: {step.get('status')}")
        name = step.get("name")
        if not isinstance(name, str) or not name.strip():
            return error(f"steps[{idx}].name inválido")
        names.append(name)
        parsed_steps.append({"name": name, "status": step["status"]})

    generated_at_utc = payload.get("generated_at_utc")
    if generated_at_utc is not None and not isinstance(generated_at_utc, str):
        return error("generated_at_utc debe ser string o null")

    inputs_used = payload.get("inputs_used")
    if inputs_used is not None:
        if not isinstance(inputs_used, dict):
            return error("inputs_used debe ser objeto")
        for key, value in inputs_used.items():
            if not isinstance(key, str) or not key.strip():
                return error("inputs_used contiene clave inválida")
            if not isinstance(value, str):
                return error(f"inputs_used[{key}] debe ser string")

    warnings = payload.get("warnings")
    if warnings is not None:
        if not isinstance(warnings, list):
            return error("warnings debe ser lista")
        for idx, warning in enumerate(warnings):
            if not isinstance(warning, str) or not warning.strip():
                return error(f"warnings[{idx}] debe ser string no vacío")

    first_failing_step = payload.get("first_failing_step")
    if first_failing_step is not None:
        if not isinstance(first_failing_step, dict):
            return error("first_failing_step debe ser objeto o null")
        first_failing_name = first_failing_step.get("name")
        if not isinstance(first_failing_name, str) or not first_failing_name.strip():
            return error("first_failing_step.name inválido")
        if first_failing_step.get("status") != "FAIL":
            return error(f"first_failing_step.status inválido: esperado FAIL, recibido {first_failing_step.get('status')}")
        if first_failing_step not in parsed_steps:
            return error("first_failing_step no coincide con steps")
    elif overall == "FAIL" and not any(step["status"] == "FAIL" for step in parsed_steps):
        return error("overall=FAIL requiere al menos un paso FAIL o first_failing_step consistente")

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
