import importlib.util
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_release_gate_summary.py"
    spec = importlib.util.spec_from_file_location("synology_release_gate_summary", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_report_pass_with_two_steps():
    module = load_module()
    text = """# Synology Release Gate Report

## Preflight: PASS

```text
ok
```

## Smoke: PASS

```text
ok
```

## Resultado global

**PASS**
"""
    parsed = module.parse_report(text)
    assert parsed["overall"] == "PASS"
    assert parsed["step_count"] == 2
    assert parsed["steps"] == [
        {"name": "Preflight", "status": "PASS"},
        {"name": "Smoke", "status": "PASS"},
    ]


def test_parse_report_fail_with_failed_step():
    module = load_module()
    text = """## Preflight: PASS
## Smoke: FAIL

## Resultado global

**FAIL**
"""
    parsed = module.parse_report(text)
    assert parsed["overall"] == "FAIL"
    assert parsed["steps"][1] == {"name": "Smoke", "status": "FAIL"}


def test_parse_report_unknown_when_no_summary_present():
    module = load_module()
    text = """# Synology Release Gate Report
Sin pasos parseables
"""
    parsed = module.parse_report(text)
    assert parsed["overall"] == "UNKNOWN"
    assert parsed["step_count"] == 0
    assert parsed["steps"] == []


def test_parse_report_ignores_markers_inside_code_fence():
    module = load_module()
    text = """## Preflight: PASS

```text
## FakeStep: FAIL
**FAIL**
```

## Resultado global

**PASS**
"""
    parsed = module.parse_report(text)
    assert parsed["overall"] == "PASS"
    assert parsed["step_count"] == 1
    assert parsed["steps"] == [{"name": "Preflight", "status": "PASS"}]
