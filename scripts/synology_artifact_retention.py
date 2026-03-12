#!/usr/bin/env python3
"""Política de retención para artifacts operacionales Synology.

Ejemplo:
  python3 scripts/synology_artifact_retention.py \
    --artifacts-dir artifacts \
    --keep-days 45 \
    --report-path artifacts-retention/synology-artifact-retention.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


@dataclass
class Item:
    path: str
    size_bytes: int
    modified_at: str


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.2f} {units[idx]}"


def write_report(report_path: Path, report: dict) -> bool:
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return True
    except OSError as exc:
        print(
            f"⚠️ No se pudo escribir reporte en {report_path}: {exc}",
            file=sys.stderr,
        )
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", default="artifacts", help="Directorio raíz de artifacts")
    parser.add_argument("--keep-days", type=int, default=45, help="Días a conservar")
    parser.add_argument("--dry-run", action="store_true", help="No elimina, sólo reporta")
    parser.add_argument(
        "--report-path",
        default="artifacts-retention/synology-artifact-retention.json",
        help="Ruta de salida del reporte JSON (fuera de artifacts)",
    )
    args = parser.parse_args()

    if args.keep_days < 1:
        parser.error(f"--keep-days debe ser al menos 1, recibido: {args.keep_days}")

    artifacts_dir = Path(args.artifacts_dir)
    report_path = Path(args.report_path)

    artifacts_abs = artifacts_dir.resolve()
    report_abs = report_path.resolve()
    if report_abs == artifacts_abs or artifacts_abs in report_abs.parents:
        parser.error(
            "--report-path debe quedar fuera de --artifacts-dir para preservar trazabilidad histórica"
        )
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.keep_days)

    report = {
        "generated_at": now.isoformat(),
        "artifacts_dir": str(artifacts_dir),
        "artifacts_dir_exists": artifacts_dir.exists(),
        "keep_days": args.keep_days,
        "dry_run": args.dry_run,
        "cutoff_utc": cutoff.isoformat(),
        "deleted_count": 0,
        "deleted_bytes": 0,
        "kept_count": 0,
        "kept_bytes": 0,
        "cleaned_empty_dirs_count": 0,
        "errors_count": 0,
        "errors": [],
        "deleted": [],
        "kept": [],
    }

    if not artifacts_dir.exists():
        print(f"ℹ️ No existe directorio de artifacts: {artifacts_dir}")
        if write_report(report_path, report):
            print(f"report_path={report_path}")
            return
        raise SystemExit(1)

    for path in sorted(p for p in artifacts_dir.rglob("*") if p.is_file()):
        if path.name == ".gitkeep":
            continue

        try:
            stat = path.stat()
        except FileNotFoundError:
            # Archivo eliminado por otro proceso entre el listado y el stat.
            continue
        except OSError as exc:
            report["errors"].append({"path": str(path), "stage": "stat", "error": str(exc)})
            report["errors_count"] += 1
            continue

        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        item = Item(
            path=str(path),
            size_bytes=stat.st_size,
            modified_at=iso(stat.st_mtime),
        )

        if modified < cutoff:
            item_dict = asdict(item)
            if not args.dry_run:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    report["errors"].append({"path": str(path), "stage": "unlink", "error": str(exc)})
                    report["errors_count"] += 1
                    continue

            report["deleted"].append(item_dict)
            report["deleted_count"] += 1
            report["deleted_bytes"] += stat.st_size
        else:
            report["kept"].append(asdict(item))
            report["kept_count"] += 1
            report["kept_bytes"] += stat.st_size

    if not args.dry_run:
        for d in sorted((p for p in artifacts_dir.rglob("*") if p.is_dir()), reverse=True):
            try:
                if any(d.iterdir()):
                    continue
            except FileNotFoundError:
                # Directorio eliminado por otro proceso en carrera.
                continue
            except OSError as exc:
                report["errors"].append({"path": str(d), "stage": "iterdir", "error": str(exc)})
                report["errors_count"] += 1
                continue

            try:
                d.rmdir()
                report["cleaned_empty_dirs_count"] += 1
            except FileNotFoundError:
                continue
            except OSError as exc:
                report["errors"].append({"path": str(d), "stage": "rmdir", "error": str(exc)})
                report["errors_count"] += 1

    if not write_report(report_path, report):
        raise SystemExit(1)

    action = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"retention={action}")
    print(f"deleted_count={report['deleted_count']}")
    print(f"deleted_bytes={report['deleted_bytes']} ({human_bytes(report['deleted_bytes'])})")
    print(f"kept_count={report['kept_count']}")
    print(f"kept_bytes={report['kept_bytes']} ({human_bytes(report['kept_bytes'])})")
    print(f"cleaned_empty_dirs_count={report['cleaned_empty_dirs_count']}")
    print(f"errors_count={report['errors_count']}")
    print(f"report_path={report_path}")


if __name__ == "__main__":
    main()
