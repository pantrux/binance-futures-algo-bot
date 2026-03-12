import importlib.util
import json
import sys
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "synology_resilience_backup.py"
    spec = importlib.util.spec_from_file_location("synology_resilience_backup", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_paths_filters_empty_values():
    module = load_module()
    assert module.parse_paths("a,b,, c ") == ["a", "b", "c"]


def test_main_generates_bundle_and_manifest_with_verify(monkeypatch, tmp_path):
    module = load_module()

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "infra/docker/synology").mkdir(parents=True)
    (repo / "docs/plans").mkdir(parents=True)

    (repo / "infra/docker/synology/docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (repo / "infra/docker/synology/.env.example").write_text("A=B\n", encoding="utf-8")
    (repo / "Makefile").write_text("all:\n\t@echo ok\n", encoding="utf-8")
    (repo / "docs/plans/synology-runbook.md").write_text("# runbook\n", encoding="utf-8")

    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "script.py",
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--verify-restore",
        ],
    )

    assert module.main() == 0

    manifest_path = out_dir / "synology-critical-config-backup-manifest.json"
    bundle_path = out_dir / "synology-critical-config-backup.tar.gz"

    assert manifest_path.exists()
    assert bundle_path.exists()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["included_count"] == 4
    assert data["missing_count"] == 0
    assert data["verify_status"] == "ok"


def test_main_returns_1_when_no_files_can_be_included(monkeypatch, tmp_path):
    module = load_module()

    repo = tmp_path / "repo"
    repo.mkdir()
    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "script.py",
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--paths",
            "missing.txt",
        ],
    )

    assert module.main() == 1


def test_main_returns_1_when_backup_is_partial(monkeypatch, tmp_path):
    module = load_module()

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "infra/docker/synology").mkdir(parents=True)
    (repo / "infra/docker/synology/docker-compose.yml").write_text("services: {}\n", encoding="utf-8")

    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "script.py",
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--paths",
            "infra/docker/synology/docker-compose.yml,missing.txt",
        ],
    )

    assert module.main() == 1


def test_main_returns_1_when_verify_restore_detects_hash_mismatch(monkeypatch, tmp_path):
    module = load_module()

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "infra/docker/synology").mkdir(parents=True)
    (repo / "docs/plans").mkdir(parents=True)

    (repo / "infra/docker/synology/docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (repo / "infra/docker/synology/.env.example").write_text("A=B\n", encoding="utf-8")
    (repo / "Makefile").write_text("all:\n\t@echo ok\n", encoding="utf-8")
    (repo / "docs/plans/synology-runbook.md").write_text("# runbook\n", encoding="utf-8")

    original_sha = module.sha256_file

    def fake_sha(path):
        if "synology-backup-verify-" in str(path):
            return "deadbeef"
        return original_sha(path)

    monkeypatch.setattr(module, "sha256_file", fake_sha)

    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "script.py",
            "--repo-root",
            str(repo),
            "--output-dir",
            str(out_dir),
            "--verify-restore",
        ],
    )

    assert module.main() == 1

    manifest = json.loads((out_dir / "synology-critical-config-backup-manifest.json").read_text(encoding="utf-8"))
    assert manifest["verify_status"] == "failed"
    assert manifest["verify_errors_count"] > 0
