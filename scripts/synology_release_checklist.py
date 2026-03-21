#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path


def current_git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def sanitize_markdown_inline(value: str, default: str = "") -> str:
    sanitized = value.replace("\r", " ").replace("\n", " ").strip()
    sanitized = sanitized.replace("`", "'")
    return sanitized if sanitized else default


def build_content(output_path: Path) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    web_base_url = os.getenv("WEB_BASE_URL", "http://127.0.0.1:3000")
    env_file = os.getenv("ENV_FILE", "infra/docker/synology/.env")
    strict_external = os.getenv("STRICT_EXTERNAL_CHECKS", "true")
    require_secrets = os.getenv("REQUIRE_SECRETS", "false")
    release_ref = os.getenv("RELEASE_REF", current_git_sha())
    signoff_owner = sanitize_markdown_inline(os.getenv("SIGNOFF_OWNER", "pending"), default="pending")
    signoff_notes = sanitize_markdown_inline(os.getenv("SIGNOFF_NOTES", ""), default="")

    return f"""# Synology Release Checklist

- Generated: {now}
- Release ref: `{release_ref}`
- API_BASE_URL: `{api_base_url}`
- WEB_BASE_URL: `{web_base_url}`
- ENV_FILE: `{env_file}`
- REQUIRE_SECRETS: `{require_secrets}`
- STRICT_EXTERNAL_CHECKS: `{strict_external}`
- Output file: `{output_path}`
- Sign-off owner (preload): `{signoff_owner}`

## 1) Preflight (configuración)
- [ ] `make synology-preflight ENV_FILE={env_file} REQUIRE_SECRETS={require_secrets}` ejecutado sin errores.
- [ ] `PAPER_TRADING=true` validado en preflight.
- [ ] Variables mínimas presentes (`DATA_ROOT`, `POSTGRES_*`, `API_PORT`, `WEB_PORT`, etc.).

## 2) Smoke (funcional)
- [ ] `make synology-smoke API_BASE_URL={api_base_url} WEB_BASE_URL={web_base_url} STRICT_EXTERNAL_CHECKS={strict_external}` en verde.
- [ ] `/health`, `/dashboard/summary`, `/trade-plans`, `/metrics` responden OK.
- [ ] Si `STRICT_EXTERNAL_CHECKS=false`, justificar en reporte por qué se flexibilizó.

## 3) Release gate unificado
- [ ] `make synology-release-gate` ejecutado.
- [ ] Reporte Markdown generado (`artifacts/synology-release-gate.md`).
- [ ] Resumen JSON generado (`artifacts/synology-release-gate.json`).
- [ ] Verificación estructural JSON (`make synology-release-verify`) en verde.

## 4) Evidencia y documentación
- [ ] Artifact de workflow descargable y consistente.
- [ ] Roadmap de PR actualizado.
- [ ] Roadmap de implementación (Gantt) actualizado.
- [ ] Si hubo cambios documentales/operativos relevantes, Outline sincronizado (runbook/roadmap/ADRs aplicables).
- [ ] Evidencia registrada usando `docs/templates/synology-deploy-evidence-template.md` o equivalente.

### 4.1) Evidencia de despliegue en NAS
- [ ] Commit SHA desplegado registrado.
- [ ] `docker compose ps` adjunto o referenciado.
- [ ] `docker compose images` adjunto o referenciado.
- [ ] Estado esperado de jobs one-shot (`migrate`, `worker`) validado.

## 5) Sign-off final
- [ ] Gate operacional aprobado para operación controlada (sin live trading).
- [ ] Fecha/hora de aprobación documentada.
- [ ] Responsable de aprobación registrado.

### Registro de aprobación
- Aprobado por: {signoff_owner}
- Fecha/hora:
- Observaciones: {signoff_notes}
"""


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/synology-release-checklist.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_content(output), encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
