import importlib.util
from pathlib import Path

import pytest


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_smoke_context_check.py"
    spec = importlib.util.spec_from_file_location("synology_smoke_context_check", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def smoke_context_module():
    return load_module()


def build_payload(*, latest_risk_context=None, recent_risk_events=None, operation_snapshots=None):
    return {
        "operation_snapshots": operation_snapshots
        if operation_snapshots is not None
        else [
            {
                "order_history": [],
                "position_history": [],
                "risk_event_history": [],
                "timeline_history": [],
                "reconciliation_recommended_actions": [],
                "latest_risk_context": latest_risk_context,
            }
        ],
        "recent_risk_events": recent_risk_events if recent_risk_events is not None else [],
    }


def test_validate_command_center_payload_detects_non_empty_operation_context(smoke_context_module):
    payload = build_payload(latest_risk_context={"symbol": "BTCUSDT"})

    assert smoke_context_module.validate_command_center_payload(payload) is True


def test_validate_command_center_payload_detects_non_empty_recent_context(smoke_context_module):
    payload = build_payload(recent_risk_events=[{"context": {"side": "BUY"}}])

    assert smoke_context_module.validate_command_center_payload(payload) is True


def test_validate_command_center_payload_allows_clean_payload_without_context(smoke_context_module):
    payload = build_payload(
        latest_risk_context={},
        recent_risk_events=[{"context": {}}, {"context": None}],
    )

    assert smoke_context_module.validate_command_center_payload(payload) is False


def test_validate_command_center_payload_requires_context_key_in_all_recent_events(smoke_context_module):
    payload = build_payload(recent_risk_events=[{"context": {}}, {"message": "missing"}])

    with pytest.raises(ValueError, match=r"recent_risk_events\[\*\] no expone context"):
        smoke_context_module.validate_command_center_payload(payload)


def test_validate_command_center_payload_still_validates_recent_events_when_snapshots_are_empty(smoke_context_module):
    payload = build_payload(operation_snapshots=[], recent_risk_events=[{"message": "missing"}])

    with pytest.raises(ValueError, match=r"recent_risk_events\[\*\] no expone context"):
        smoke_context_module.validate_command_center_payload(payload)


def test_main_returns_expected_flag_for_clean_payload(smoke_context_module, monkeypatch, tmp_path, capsys):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        '{"operation_snapshots":[{"order_history":[],"position_history":[],"risk_event_history":[],"timeline_history":[],"reconciliation_recommended_actions":[],"latest_risk_context":{}}],"recent_risk_events":[{"context":{}}]}',
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["synology_smoke_context_check.py", str(payload_path)])

    assert smoke_context_module.main() == 0
    output = capsys.readouterr().out
    assert "HAS_NON_EMPTY_CONTEXT=0" in output


def test_main_returns_expected_flag_for_non_empty_context(smoke_context_module, monkeypatch, tmp_path, capsys):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        '{"operation_snapshots":[{"order_history":[],"position_history":[],"risk_event_history":[],"timeline_history":[],"reconciliation_recommended_actions":[],"latest_risk_context":{"symbol":"BTCUSDT"}}],"recent_risk_events":[]}',
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["synology_smoke_context_check.py", str(payload_path)])

    assert smoke_context_module.main() == 0
    output = capsys.readouterr().out
    assert "HAS_NON_EMPTY_CONTEXT=1" in output
