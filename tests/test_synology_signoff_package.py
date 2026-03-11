import importlib.util
import json
import sys
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_signoff_package.py"
    spec = importlib.util.spec_from_file_location("synology_signoff_package", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_generates_package(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(
        json.dumps(
            {
                "overall": "PASS",
                "step_count": 2,
                "steps": [
                    {"name": "Preflight", "status": "PASS"},
                    {"name": "Smoke", "status": "PASS"},
                ],
            }
        ),
        encoding="utf-8",
    )
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 0
    assert out.exists()
    body = out.read_text(encoding="utf-8")
    assert "Synology Sign-off Package" in body
    assert "overall: **PASS**" in body


def test_main_returns_1_on_missing_input(tmp_path, monkeypatch):
    module = load_module()
    missing = tmp_path / "missing.md"

    monkeypatch.setattr(sys, "argv", ["script.py", str(missing), str(missing), str(missing)])
    assert module.main() == 1
