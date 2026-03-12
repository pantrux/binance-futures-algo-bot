#!/usr/bin/env python3
"""Genera evidencia de backup/recovery para configuración crítica Synology.

Este script crea:
1) bundle tar.gz con archivos críticos,
2) manifest JSON con hashes SHA-256, RTO/RPO objetivo y resultado de verificación.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATHS = [
    "infra/docker/synology/docker-compose.yml",
    "infra/docker/synology/.env.example",
    "Makefile",
    "docs/plans/synology-runbook.md",
]


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_paths(raw: str) -> list[str]:
    items = [p.strip() for p in raw.split(",")]
    return [p for p in items if p]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backup verificable de configuración Synology")
    parser.add_argument("--repo-root", default=".", help="Raíz del repositorio")
    parser.add_argument(
        "--paths",
        default=",".join(DEFAULT_PATHS),
        help="Lista CSV de rutas relativas a incluir en el backup",
    )
    parser.add_argument("--output-dir", default="artifacts-resilience", help="Directorio de salida")
    parser.add_argument(
        "--bundle-name",
        default="synology-critical-config-backup.tar.gz",
        help="Nombre del bundle tar.gz",
    )
    parser.add_argument(
        "--manifest-name",
        default="synology-critical-config-backup-manifest.json",
        help="Nombre del manifest JSON",
    )
    parser.add_argument("--rto-minutes", type=int, default=60, help="Objetivo RTO en minutos")
    parser.add_argument("--rpo-minutes", type=int, default=1440, help="Objetivo RPO en minutos")
    parser.add_argument(
        "--verify-restore",
        action="store_true",
        help="Extrae bundle en directorio temporal y verifica hashes",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.rto_minutes < 1 or args.rpo_minutes < 1:
        parser.error("--rto-minutes y --rpo-minutes deben ser >= 1")

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    requested_paths = parse_paths(args.paths)
    if not requested_paths:
        parser.error("--paths no puede estar vacío")

    included: list[dict[str, str | int]] = []
    missing: list[str] = []

    for rel in requested_paths:
        full_path = (repo_root / rel).resolve()
        try:
            full_path.relative_to(repo_root)
        except ValueError:
            parser.error(f"Ruta fuera de repo-root no permitida: {rel}")

        if not full_path.exists() or not full_path.is_file():
            missing.append(rel)
            continue

        included.append(
            {
                "path": rel,
                "size_bytes": full_path.stat().st_size,
                "sha256": sha256_file(full_path),
            }
        )

    if not included:
        print("❌ No hay archivos válidos para respaldar")
        return 1

    bundle_path = output_dir / args.bundle_name
    manifest_path = output_dir / args.manifest_name

    with tarfile.open(bundle_path, mode="w:gz") as tar:
        for item in included:
            rel_path = item["path"]
            tar.add(repo_root / rel_path, arcname=rel_path)

    verify_status = "skipped"
    verify_errors: list[str] = []

    if args.verify_restore:
        verify_status = "ok"
        with tempfile.TemporaryDirectory(prefix="synology-backup-verify-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            with tarfile.open(bundle_path, mode="r:gz") as tar:
                tar.extractall(tmp_root, filter="data")

            for item in included:
                rel_path = item["path"]
                restored = tmp_root / rel_path
                if not restored.exists():
                    verify_status = "failed"
                    verify_errors.append(f"No existe restaurado: {rel_path}")
                    continue

                restored_hash = sha256_file(restored)
                if restored_hash != item["sha256"]:
                    verify_status = "failed"
                    verify_errors.append(f"Hash mismatch en {rel_path}")

    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "generated_at": generated_at,
        "repo_root": str(repo_root),
        "bundle_path": str(bundle_path),
        "manifest_path": str(manifest_path),
        "targets_count": len(requested_paths),
        "included_count": len(included),
        "missing_count": len(missing),
        "missing": missing,
        "rto_minutes": args.rto_minutes,
        "rpo_minutes": args.rpo_minutes,
        "verify_restore": args.verify_restore,
        "verify_status": verify_status,
        "verify_errors_count": len(verify_errors),
        "verify_errors": verify_errors,
        "files": included,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"included_count={manifest['included_count']}")
    print(f"missing_count={manifest['missing_count']}")
    print(f"verify_status={manifest['verify_status']}")
    print(f"bundle_path={bundle_path}")
    print(f"manifest_path={manifest_path}")

    if missing:
        print(f"❌ Archivos no encontrados en el backup: {missing}")
        return 1
    if verify_status == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
