# Runbook Synology — arranque inicial y demo loop

## Objetivo
Levantar el stack completo en el NAS y poblar un conjunto mínimo de trade plans / paper executions para validar el circuito completo.

## Secuencia
1. Copiar repo al NAS.
2. Configurar `infra/docker/synology/.env`.
3. Ejecutar preflight de configuración:
   - `ENV_FILE=infra/docker/synology/.env ./scripts/synology_preflight_check.sh`
4. Ejecutar `docker compose up -d --build`.
5. Verificar que `migrate` termine OK.
6. Verificar `api` y `web` saludables.
7. Ejecutar seed/demo si se desea poblar datos:
   - `docker compose exec worker python /app/scripts/seed_demo_data.py`
8. Abrir el dashboard web y validar resumen + últimos trade plans.

## Contenedores esperados
- `trading-bot-postgres`
- `trading-bot-redis`
- `trading-bot-migrate` *(one-shot; debe quedar en `Exited (0)`)*
- `trading-bot-api`
- `trading-bot-worker` *(one-shot; debe quedar en `Exited (0)`)*
- `trading-bot-web`

## Modelo operativo validado (post PR-20)
- Servicios persistentes 24/7: `api`, `web`, `postgres`, `redis`.
- Jobs one-shot: `migrate` y `worker`.
- En Synology, `worker` se ejecuta sin restart loop (`restart: "no"`) para evitar corridas infinitas.

## Verificaciones clave
- `/health`
- `/dashboard/summary`
- `/trade-plans`
- `/integrations/binance/testnet/ping`
- `/metrics` (con o sin `x-metrics-key`, según configuración)
- documentos en Outline creados por los trade plans

## Preflight automático (PR-10)

```bash
ENV_FILE=infra/docker/synology/.env \
./scripts/synology_preflight_check.sh
```

Opcional (modo estricto de secretos):

```bash
ENV_FILE=infra/docker/synology/.env \
REQUIRE_SECRETS=true \
./scripts/synology_preflight_check.sh
```

Opcional para entornos sin Docker local (solo validar `.env`):

```bash
ENV_FILE=infra/docker/synology/.env \
SKIP_COMPOSE_VALIDATION=true \
./scripts/synology_preflight_check.sh
```

También disponible por GitHub Actions (`Synology Preflight`, `workflow_dispatch`).

> Seguridad: `synology_preflight_check.sh` carga `ENV_FILE` con `source`; úsalo solo con archivos de entorno confiables.

## Release gate unificado (PR-11)

```bash
ENV_FILE=infra/docker/synology/.env \
API_BASE_URL="http://IP_NAS:API_PORT" \
WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
./scripts/synology_release_gate.sh
```

Equivalente con Make:

```bash
make synology-release-gate \
  ENV_FILE=infra/docker/synology/.env \
  API_BASE_URL="http://IP_NAS:API_PORT" \
  WEB_BASE_URL="http://IP_NAS:WEB_PORT"
```

Genera reporte Markdown en `artifacts/synology-release-gate.md`.

Para resumen máquina-legible:

```bash
python3 scripts/synology_release_gate_summary.py \
  artifacts/synology-release-gate.md \
  artifacts/synology-release-gate.json
```

Para validar consistencia estructural del JSON:

```bash
python3 scripts/synology_release_gate_verify.py \
  artifacts/synology-release-gate.json \
  "Preflight,Smoke"
```

Atajos Make:

```bash
make synology-release-summary REPORT_PATH=artifacts/synology-release-gate.md
make synology-release-verify EXPECTED_STEPS="Preflight,Smoke"
make synology-release-checklist CHECKLIST_PATH=artifacts/synology-release-checklist.md
make synology-signoff-package \
  REPORT_PATH=artifacts/synology-release-gate.md \
  JSON_PATH=artifacts/synology-release-gate.json \
  CHECKLIST_PATH=artifacts/synology-release-checklist.md \
  PACKAGE_PATH=artifacts/synology-signoff-package.md
make synology-signoff-all \
  ENV_FILE=infra/docker/synology/.env \
  API_BASE_URL="http://IP_NAS:API_PORT" \
  WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
  SIGNOFF_OWNER="<responsable>"
```

## Cierre formal de fase 5

El cierre operativo formal de esta fase está documentado en:
- [`docs/plans/phase5-operational-closure.md`](./phase5-operational-closure.md)

## Retención de artifacts operacionales (PR-22)

Ejecución manual (dry-run):

```bash
make synology-artifact-retention \
  ARTIFACTS_DIR=artifacts \
  KEEP_DAYS=45 \
  RETENTION_DRY_RUN=true
```

Aplicar eliminación real:

```bash
make synology-artifact-retention \
  ARTIFACTS_DIR=artifacts \
  KEEP_DAYS=45 \
  RETENTION_DRY_RUN=false
```

Reporte JSON generado por defecto (fuera de `artifacts/` para conservar historial):
- `artifacts-retention/synology-artifact-retention.json`

También disponible workflow de GitHub Actions:
- `Synology Artifact Retention` (`workflow_dispatch` + `schedule` diario, siempre en dry-run)

> Nota: la eliminación real (`RETENTION_DRY_RUN=false`) debe ejecutarse en Synology, donde existe el directorio real de artifacts.

## Observabilidad y alerting operacional (PR-23)

Ejecución manual local:

```bash
GH_TOKEN="<github_token>" \
make synology-operational-observability \
  OPS_REPO=pantrux/binance-futures-algo-bot \
  OPS_WINDOW_HOURS=168 \
  OPS_MIN_SUCCESS_RATE=0.90 \
  OPS_MIN_RUNS=1 \
  OPS_DRIFT_WORKFLOWS="Synology Artifact Retention"
```

Health checks opcionales (si el endpoint es alcanzable desde donde se ejecuta):

```bash
GH_TOKEN="<github_token>" \
make synology-operational-observability \
  OPS_REPO=pantrux/binance-futures-algo-bot \
  OPS_HEALTH_API_URL="https://pantrux.duckdns.org/dashboard/health" \
  OPS_HEALTH_WEB_URL="https://pantrux.duckdns.org/dashboard/"
```

Artifacts generados:
- `artifacts/synology-operational-observability.json`
- `artifacts/synology-operational-observability.md`

Workflow disponible:
- `Synology Observability & Alerting` (`workflow_dispatch` + `schedule` horario)

Variables opcionales de repo para health checks desde CI:
- `SYNOLOGY_HEALTH_API_URL`
- `SYNOLOGY_HEALTH_WEB_URL`

> El workflow falla explícitamente cuando detecta alertas (SLO degradado, drift operativo o health fallido).

## Resiliencia y recovery de configuración crítica (PR-24)

Generar evidencia de backup + verificación de restore:

```bash
make synology-resilience-backup \
  RESILIENCE_VERIFY_RESTORE=true \
  RESILIENCE_RTO_MINUTES=60 \
  RESILIENCE_RPO_MINUTES=1440
```

Artifacts esperados:
- `artifacts-resilience/synology-critical-config-backup.tar.gz`
- `artifacts-resilience/synology-critical-config-backup-manifest.json`

Workflow disponible:
- `Synology Resilience Backup Verify` (`workflow_dispatch` + `schedule` diario)

Campos clave del manifest a revisar en cada corrida:
- `verify_status` (debe ser `ok`)
- `missing_count` (debe ser `0` para cobertura completa)
- `rto_minutes` / `rpo_minutes` (alineados al objetivo operativo vigente)

> Alcance actual: configuración crítica del repositorio. El DR completo de datos runtime del NAS se mantendrá como siguiente expansión de hardening.

## Sync de documentación en Outline (sin duplicados)

```bash
OUTLINE_API_TOKEN="..." \
python3 scripts/sync_outline_docs.py
```

El sync reescribe links locales del repo a URLs navegables:
- **preferencia:** documento equivalente en Outline
- **fallback:** URL web del repo (`blob/<ref>`; imágenes vía `raw.githubusercontent.com`)
- **alcance:** solo fuera de bloques de código cercados (respetando el delimitador real del fence) y preservando spans inline con backticks simples o múltiples
- **heurística documentada:** rutas que empiecen por `docs/` o `scripts/` se interpretan como relativas a la raíz del repo; el resto sigue la resolución relativa al documento origen

Variables opcionales:
- `OUTLINE_REPO_WEB_BASE` para forzar la base web del repo (acepta tanto la URL del repo como `.../blob/<ref>`)
- `OUTLINE_GIT_REF` para elegir la ref usada en links GitHub/raw (default `main`)

Limpieza opcional de documentos legacy fuera del catálogo oficial:

```bash
OUTLINE_API_TOKEN="..." \
python3 scripts/sync_outline_docs.py --archive-unknown
```

## Smoke test automático (PR-9)

Desde la raíz del repositorio:

```bash
API_BASE_URL="http://IP_NAS:API_PORT" \
WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
METRICS_API_KEY="<opcional>" \
./scripts/synology_smoke_test.sh
```

### Criterio mínimo de aprobación
1. Todos los checks del script en verde.
2. `docker compose ps` sin servicios `unhealthy`.
3. Dashboard responde y muestra resumen sin errores 5xx.
4. API responde `testnet/ping` correctamente.
5. Gate C de shadow run puede evaluarse con artifact auditable (`synology-shadow-run-gate`).
6. No activar live trading; mantener `PAPER_TRADING=true`.

> Nota operativa: `/integrations/binance/testnet/ping` depende de disponibilidad externa de Binance Testnet.
> Si Binance está intermitente, repetir el smoke o ejecutar temporalmente con `STRICT_EXTERNAL_CHECKS=false`
> para no bloquear validaciones internas del NAS por una caída externa puntual.

## Gate C — Shadow run readiness

Para evaluar readiness antes de iniciar testnet serio o decidir avance hacia real-micro:

1. Ejecutar el workflow `.github/workflows/synology-shadow-run-gate.yml` o correr localmente:
   - `python3 scripts/synology_shadow_run_gate.py --api-base-url <API> --metrics-api-key <KEY>`
2. Revisar artifact JSON + Markdown generado.
3. Confirmar umbrales mínimos:
   - `>= 7` días observados de shadow run
   - `>= 200` trades paper
   - `>= 200` trades testnet
   - `>= 200` pares comparados
   - fill rate testnet `>= 98%`
   - `0` eventos críticos en 7d
   - `<= 3` warnings en 7d
   - promedio de risk events 30d `<= 1/día`
4. Adjuntar el artifact al checkpoint operativo/cutover correspondiente.

### Estado real validado tras despliegue de PR-41
- Endpoint `GET /reporting/shadow-run-summary` desplegado y operativo en `<API_BASE_URL>` (por ejemplo, `http://192.168.0.8:8010` en el NAS local).
- Primer gate real ejecutado: `paper=63`, `testnet=0`, `duration_days=3.0494`, `overall=FAIL`.
- Bloqueo detectado en NAS: `BINANCE_API_KEY` y `BINANCE_API_SECRET` vacíos en `infra/docker/synology/.env`.
- Mientras ese bloqueo persista, el bot seguirá generando solo `paper_executed` y no habrá evidencia testnet útil para Gate C.

## Troubleshooting real validado en Synology
- Si `docker compose` falla con `build context` inválido desde `infra/docker/synology`, validar que el compose use `context: ../../../`.
- Si Redis cae con `Can't open or create append-only dir appendonlydir: Permission denied`, usar `--appendonly no` para operación en este entorno NAS.
- Si `migrate` falla con `No 'script_location' key found`, validar que imagen API incluya `alembic.ini` y carpeta `alembic/`.
- Si `migrate` intenta `localhost:5432`, validar que `alembic/env.py` lea `POSTGRES_DSN` desde environment.
- Si build falla leyendo `data/postgres` (`can't stat`), agregar `.dockerignore` excluyendo `data/`.
