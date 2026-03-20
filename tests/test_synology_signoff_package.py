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
                "inputs_used": {
                    "API_BASE_URL": "http://nas/api",
                    "WEB_BASE_URL": "http://nas/web",
                },
                "warnings": [],
                "first_failing_step": None,
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
    assert "Gate aprobado; el paquete soporta sign-off operacional." in body
    assert "API_BASE_URL: `http://nas/api`" in body
    assert "WEB_BASE_URL: `http://nas/web`" in body
    assert body.index("API_BASE_URL: `http://nas/api`") < body.index("WEB_BASE_URL: `http://nas/web`")
    assert "overall: **PASS**" in body
    assert "Sin warnings derivados del reporte." in body
    assert "Registrar aprobación final en el checklist" in body
    assert "estructura validada y apta para decisión operativa" in body


def test_main_generates_failure_recommendation(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(
        json.dumps(
            {
                "overall": "FAIL",
                "step_count": 2,
                "steps": [
                    {"name": "Preflight", "status": "PASS"},
                    {"name": "Smoke", "status": "FAIL"},
                ],
                "warnings": ["Preflight fallido - smoke omitido para evitar ruido diagnóstico."],
                "first_failing_step": {"name": "Smoke", "status": "FAIL"},
            }
        ),
        encoding="utf-8",
    )
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 0
    body = out.read_text(encoding="utf-8")
    assert "Gate no aprobado; el sign-off debe quedar bloqueado" in body
    assert "Smoke: FAIL" in body
    assert "Preflight fallido - smoke omitido para evitar ruido diagnóstico." in body
    assert "Corregir el paso `Smoke` y reejecutar `make synology-signoff-all`" in body


def test_main_returns_1_on_missing_input(tmp_path, monkeypatch):
    module = load_module()
    missing = tmp_path / "missing.md"

    monkeypatch.setattr(sys, "argv", ["script.py", str(missing), str(missing), str(missing)])
    assert module.main() == 1


def test_main_returns_1_on_missing_json_fields(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(json.dumps({"overall": "PASS"}), encoding="utf-8")
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 1


def test_main_returns_1_on_invalid_json_root_type(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(json.dumps([{"overall": "PASS"}]), encoding="utf-8")
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 1


def test_main_returns_1_on_invalid_json_types(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(
        json.dumps({"overall": None, "step_count": True, "steps": "bad"}),
        encoding="utf-8",
    )
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 1


def test_main_returns_1_on_invalid_optional_json_fields(tmp_path, monkeypatch):
    module = load_module()

    gate_md = tmp_path / "gate.md"
    gate_json = tmp_path / "gate.json"
    checklist = tmp_path / "checklist.md"
    out = tmp_path / "package.md"

    gate_md.write_text("# gate", encoding="utf-8")
    gate_json.write_text(
        json.dumps(
            {
                "overall": "FAIL",
                "step_count": 1,
                "steps": [{"name": "Preflight", "status": "FAIL"}],
                "warnings": [""],
            }
        ),
        encoding="utf-8",
    )
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 1


def test_main_returns_1_when_steps_contains_non_dict(tmp_path, monkeypatch):
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
                "step_count": 1,
                "steps": ["bad-step"],
            }
        ),
        encoding="utf-8",
    )
    checklist.write_text("# checklist", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["script.py", str(gate_md), str(gate_json), str(checklist), str(out)])
    assert module.main() == 1
