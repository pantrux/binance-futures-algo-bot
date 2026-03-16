from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_OPERATION_FIELDS = [
    "order_history",
    "position_history",
    "risk_event_history",
    "timeline_history",
    "reconciliation_recommended_actions",
    "latest_risk_context",
]


def validate_command_center_payload(payload: dict[str, Any]) -> bool:
    ops = payload.get("operation_snapshots")
    if not isinstance(ops, list):
        raise ValueError("operation_snapshots no es lista")

    has_non_empty_context = False
    if not ops:
        print("WARN_EMPTY_OPERATION_SNAPSHOTS")
    else:
        op = ops[0]
        missing = [key for key in REQUIRED_OPERATION_FIELDS if key not in op]
        if missing:
            raise ValueError(f"faltan campos en operation_snapshot: {missing}")
        if not isinstance(op["timeline_history"], list):
            raise ValueError("timeline_history no es lista")
        if len(op["timeline_history"]) > 20:
            raise ValueError("timeline_history excede límite esperado de 20")
        if op["latest_risk_context"] is not None and not isinstance(op["latest_risk_context"], dict):
            raise ValueError("latest_risk_context debe ser dict o None")
        has_non_empty_context = bool(op["latest_risk_context"])

    recent = payload.get("recent_risk_events")
    if not isinstance(recent, list):
        raise ValueError("recent_risk_events no es lista")
    for item in recent:
        if "context" not in item:
            raise ValueError("recent_risk_events[*] no expone context")
        if item.get("context") is not None and not isinstance(item.get("context"), dict):
            raise ValueError("recent_risk_events[*].context debe ser dict o None")
        has_non_empty_context = has_non_empty_context or bool(item.get("context"))

    return has_non_empty_context


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("Uso: synology_smoke_context_check.py <payload.json>", file=sys.stderr)
        return 2

    payload_path = Path(argv[0])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    has_non_empty_context = validate_command_center_payload(payload)
    print("OK")
    print(f"HAS_NON_EMPTY_CONTEXT={'1' if has_non_empty_context else '0'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
