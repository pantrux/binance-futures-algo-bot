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
    assert isinstance(ops, list), "operation_snapshots no es lista"

    has_non_empty_context = False
    if not ops:
        return False

    op = ops[0]
    missing = [key for key in REQUIRED_OPERATION_FIELDS if key not in op]
    assert not missing, f"faltan campos en operation_snapshot: {missing}"
    assert isinstance(op["timeline_history"], list), "timeline_history no es lista"
    assert len(op["timeline_history"]) <= 20, "timeline_history excede límite esperado de 20"
    assert op["latest_risk_context"] is None or isinstance(
        op["latest_risk_context"], dict
    ), "latest_risk_context debe ser dict o None"
    has_non_empty_context = bool(op["latest_risk_context"])

    recent = payload.get("recent_risk_events")
    assert isinstance(recent, list), "recent_risk_events no es lista"
    for item in recent:
        assert "context" in item, "recent_risk_events[*] no expone context"
        assert item.get("context") is None or isinstance(
            item.get("context"), dict
        ), "recent_risk_events[*].context debe ser dict o None"
        has_non_empty_context = has_non_empty_context or bool(item.get("context"))

    return has_non_empty_context


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
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
