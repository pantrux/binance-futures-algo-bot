#!/usr/bin/env python3
"""Política de retención para artifacts operacionales Synology.

Ejemplo:
  python3 scripts/synology_artifact_retention.py \
    --artifacts-dir artifacts \
    --keep-days 45 \
    --report-path artifacts/synology-artifact-retention.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", default="artifacts", help="Directorio raíz de artifacts")
    parser.add_argument("--keep-days", type=int, default=45, help="Días a conservar")
    parser.add_argument("--dry-run", action="store_true", help="No elimina, sólo reporta")
    parser.add_argument(
        "--report-path",
        default="artifacts/synology-artifact-retention.json",
        help="Ruta de salida del reporte JSON",
    )
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.keep_days)

    report = {
        "generated_at": now.isoformat(),
        "artifacts_dir": str(artifacts_dir),
        "keep_days": args.keep_days,
        "dry_run": args.dry_run,
        "cutoff_utc": cutoff.isoformat(),
        "deleted_count": 0,
        "deleted_bytes": 0,
        "kept_count": 0,
        "kept_bytes": 0,
        "deleted": [],
        "kept": [],
    }

    if not artifacts_dir.exists():
        print(f"ℹ️ No existe directorio de artifacts: {artifacts_dir}")
        out = Path(args.report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"report_path={out}")
        return

    for path in sorted(p for p in artifacts_dir.rglob("*") if p.is_file()):
        if path.name == ".gitkeep":
            continue

        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        item = Item(
            path=str(path),
            size_bytes=stat.st_size,
            modified_at=iso(stat.st_mtime),
        )

        if modified < cutoff:
            report["deleted"].append(asdict(item))
            report["deleted_count"] += 1
            report["deleted_bytes"] += stat.st_size
            if not args.dry_run:
                path.unlink(missing_ok=True)
        else:
            report["kept"].append(asdict(item))
            report["kept_count"] += 1
            report["kept_bytes"] += stat.st_size

    out = Path(args.report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    action = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"retention={action}")
    print(f"deleted_count={report['deleted_count']}")
    print(f"deleted_bytes={report['deleted_bytes']} ({human_bytes(report['deleted_bytes'])})")
    print(f"kept_count={report['kept_count']}")
    print(f"kept_bytes={report['kept_bytes']} ({human_bytes(report['kept_bytes'])})")
    print(f"report_path={out}")


if __name__ == "__main__":
    main()
