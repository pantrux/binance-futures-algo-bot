import importlib.util
from pathlib import Path

import pytest


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_release_gate_verify.py"
    spec = importlib.util.spec_from_file_location("synology_release_gate_verify", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def verify_module():
    return load_module()


def test_verify_payload_pass(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 2,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "PASS"},
        ],
        "generated_at_utc": "2025-01-02 03:04:05",
        "inputs_used": {"API_BASE_URL": "http://nas/api"},
        "warnings": [],
        "first_failing_step": None,
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 0


def test_verify_payload_fails_when_step_count_mismatch(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 1,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_expected_steps_differ(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 2,
        "steps": [
            {"name": "Smoke", "status": "PASS"},
            {"name": "Preflight", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_first_failing_step_is_inconsistent(verify_module):
    payload = {
        "overall": "FAIL",
        "step_count": 2,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "FAIL"},
        ],
        "first_failing_step": {"name": "Preflight", "status": "FAIL"},
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_first_failing_step_status_is_not_fail(verify_module):
    payload = {
        "overall": "FAIL",
        "step_count": 2,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "FAIL"},
        ],
        "first_failing_step": {"name": "Smoke", "status": "PASS"},
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_inputs_used_has_non_string_value(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 1,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
        ],
        "inputs_used": {"STRICT_EXTERNAL_CHECKS": False},
    }
    assert verify_module.verify_payload(payload, ["Preflight"]) == 1


def test_verify_payload_fails_when_warnings_are_invalid(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 1,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
        ],
        "warnings": [""],
    }
    assert verify_module.verify_payload(payload, ["Preflight"]) == 1


def test_main_returns_1_for_missing_file(verify_module, monkeypatch, tmp_path):
    import sys

    missing = tmp_path / "missing.json"
    monkeypatch.setattr(sys, "argv", ["script.py", str(missing)])
    assert verify_module.main() == 1


def test_verify_payload_fails_when_root_is_not_dict(verify_module):
    assert verify_module.verify_payload(["not", "dict"], ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_overall_is_invalid(verify_module):
    payload = {
        "overall": "UNKNOWN",
        "step_count": 2,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_step_status_is_invalid(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": 2,
        "steps": [
            {"name": "Preflight", "status": "UNKNOWN"},
            {"name": "Smoke", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_step_count_is_not_int(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": "2",
        "steps": [
            {"name": "Preflight", "status": "PASS"},
            {"name": "Smoke", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight", "Smoke"]) == 1


def test_verify_payload_fails_when_step_count_is_bool(verify_module):
    payload = {
        "overall": "PASS",
        "step_count": True,
        "steps": [
            {"name": "Preflight", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, ["Preflight"]) == 1


def test_verify_payload_passes_when_expected_steps_is_empty(verify_module):
    payload = {
        "overall": "FAIL",
        "step_count": 2,
        "steps": [
            {"name": "Smoke", "status": "FAIL"},
            {"name": "Preflight", "status": "PASS"},
        ],
    }
    assert verify_module.verify_payload(payload, []) == 0


def test_main_returns_2_when_missing_args(verify_module, monkeypatch):
    import sys

    monkeypatch.setattr(sys, "argv", ["script.py"])
    assert verify_module.main() == 2


def test_main_returns_1_for_invalid_json(verify_module, monkeypatch, tmp_path):
    import sys

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["script.py", str(bad_json)])
    assert verify_module.main() == 1


def test_main_returns_0_for_valid_json(verify_module, monkeypatch, tmp_path):
    import sys

    good_json = tmp_path / "good.json"
    good_json.write_text(
        '{"overall":"PASS","step_count":2,"steps":[{"name":"Preflight","status":"PASS"},{"name":"Smoke","status":"PASS"}],"inputs_used":{"API_BASE_URL":"http://nas/api"},"warnings":[],"first_failing_step":null}',
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["script.py", str(good_json), "Preflight,Smoke"])
    assert verify_module.main() == 0
