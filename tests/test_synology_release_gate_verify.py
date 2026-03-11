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


def test_main_returns_1_for_missing_file(verify_module, monkeypatch, tmp_path):
    import sys

    missing = tmp_path / "missing.json"
    monkeypatch.setattr(sys, "argv", ["script.py", str(missing)])
    assert verify_module.main() == 1
