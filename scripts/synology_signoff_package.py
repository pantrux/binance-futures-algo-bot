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

    if data["overall"] is None:
        raise ValueError("overall no puede ser null")

    if not isinstance(data["steps"], list):
        raise ValueError("steps debe ser una lista")
    for idx, step in enumerate(data["steps"]):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{idx}] debe ser objeto")

    if not isinstance(data["step_count"], int) or isinstance(data["step_count"], bool):
        raise ValueError("step_count debe ser entero")

    warnings = data.get("warnings")
    if warnings is not None:
        if not isinstance(warnings, list):
            raise ValueError("warnings debe ser lista")
        for idx, warning in enumerate(warnings):
            if not isinstance(warning, str) or not warning.strip():
                raise ValueError(f"warnings[{idx}] debe ser string no vacío")

    first_failing_step = data.get("first_failing_step")
    if first_failing_step is not None:
        if not isinstance(first_failing_step, dict):
            raise ValueError("first_failing_step debe ser objeto o null")
        if not isinstance(first_failing_step.get("name"), str) or not first_failing_step["name"].strip():
            raise ValueError("first_failing_step.name inválido")
        if first_failing_step.get("status") != "FAIL":
            raise ValueError("first_failing_step.status debe ser FAIL")

    inputs_used = data.get("inputs_used")
    if inputs_used is not None:
        if not isinstance(inputs_used, dict):
            raise ValueError("inputs_used debe ser objeto")
        for key, value in inputs_used.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("inputs_used contiene clave inválida")
            if not isinstance(value, str):
                raise ValueError(f"inputs_used[{key}] debe ser string")

    return data


def build_executive_summary(summary: dict) -> list[str]:
    overall = summary.get("overall")
    step_count = summary.get("step_count", 0)
    failed_steps = [
        step.get("name", "unknown")
        for step in summary.get("steps", [])
        if isinstance(step, dict) and step.get("status") == "FAIL"
    ]
    warning_count = len(summary.get("warnings") or [])

    if overall == "PASS":
        headline = "Gate aprobado; el paquete soporta sign-off operacional."
    else:
        headline = "Gate no aprobado; el sign-off debe quedar bloqueado hasta corregir el primer fallo."

    details = f"Se evaluaron {step_count} pasos; fallos detectados: {len(failed_steps)}; warnings: {warning_count}."
    if failed_steps:
        details += f" Primer fallo: {failed_steps[0]}."

    return [headline, details]


def build_next_actions(summary: dict) -> list[str]:
    actions: list[str] = []
    first_failing_step = summary.get("first_failing_step")
    warnings = summary.get("warnings") or []

    if summary.get("overall") == "PASS":
        actions.append("Registrar aprobación final en el checklist y adjuntar este paquete al evidence set del release.")
    else:
        failing_name = first_failing_step.get("name") if isinstance(first_failing_step, dict) else "paso fallido"
        actions.append(f"Corregir el paso `{failing_name}` y reejecutar `make synology-signoff-all` para regenerar evidencia consistente.")

    if warnings:
        actions.append("Revisar y documentar cada warning antes del cierre, aunque el gate haya quedado en PASS.")

    if summary.get("overall") == "FAIL" and not warnings:
        actions.append("Usar `artifacts/synology-release-gate.md` para inspección detallada del log del paso fallido.")

    return actions


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

    executive_summary = build_executive_summary(summary)
    next_actions = build_next_actions(summary)
    first_failing_step = summary.get("first_failing_step")
    warnings = summary.get("warnings") or []
    inputs_used = summary.get("inputs_used") or {}

    steps_lines = []
    for step in summary.get("steps", []):
        name = step.get("name", "unknown")
        status = step.get("status", "unknown")
        steps_lines.append(f"- {name}: {status}")

    input_lines = [f"- {key}: `{inputs_used[key]}`" for key in sorted(inputs_used)]
    if not input_lines:
        input_lines.append("- Sin metadatos de entrada parseables en el reporte actual.")

    warning_lines = [f"- {warning}" for warning in sorted(warnings)]
    if not warning_lines:
        warning_lines.append("- Sin warnings derivados del reporte.")

    next_action_lines = [f"- {action}" for action in next_actions]

    first_failing_step_line = (
        f"- {first_failing_step['name']}: {first_failing_step['status']}" if isinstance(first_failing_step, dict) else "- Ninguno"
    )

    content = f"""# Synology Sign-off Package

- Generated: {generated_at}
- Gate markdown: `{gate_md}`
- Gate json: `{gate_json}`
- Checklist: `{checklist_md}`

## Resumen ejecutivo
- {executive_summary[0]}
- {executive_summary[1]}

## Inputs usados
{chr(10).join(input_lines)}

## Estado del gate
- overall: **{summary.get('overall')}**
- step_count: **{summary.get('step_count')}**
- first_failing_step:
{first_failing_step_line}

{chr(10).join(steps_lines)}

## Warnings
{chr(10).join(warning_lines)}

## Siguiente acción recomendada
{chr(10).join(next_action_lines)}

## Estado del checklist
- Archivo de checklist presente: ✅ (contenido no validado por este script)
- Archivo de gate markdown presente: ✅ (contenido no validado por este script)
- Archivo de gate json presente: ✅ (estructura validada y apta para decisión operativa)

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
