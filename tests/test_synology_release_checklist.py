import importlib.util
import os
import sys
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_release_checklist.py"
    spec = importlib.util.spec_from_file_location("synology_release_checklist", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_content_includes_core_sections(monkeypatch):
    module = load_module()
    monkeypatch.setenv("API_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("WEB_BASE_URL", "https://web.example.com")
    monkeypatch.setenv("RELEASE_REF", "abc1234")

    content = module.build_content(Path("artifacts/sample.md"))

    assert "# Synology Release Checklist" in content
    assert "## 1) Preflight (configuración)" in content
    assert "## 2) Smoke (funcional)" in content
    assert "## 3) Release gate unificado" in content
    assert "## 4) Evidencia y documentación" in content
    assert "## 5) Sign-off final" in content
    assert "`abc1234`" in content
    assert "https://api.example.com" in content


def test_main_writes_file(tmp_path, monkeypatch):
    module = load_module()
    out = tmp_path / "checklist.md"

    monkeypatch.setattr(sys, "argv", ["script.py", str(out)])
    assert module.main() == 0
    assert out.exists()

    body = out.read_text(encoding="utf-8")
    assert "Synology Release Checklist" in body
    assert "Registro de aprobación" in body
