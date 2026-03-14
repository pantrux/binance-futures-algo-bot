# Binance Futures Algo Bot

Bot de trading algorítmico para **Binance USDⓈ-M Futures** orientado a operativa automática de **scalping** e **intradía**, con enfoque de arquitectura auditable, gestión de riesgo estricta y documentación viva en Outline.

## Objetivos del MVP

- Análisis técnico, fundamental y de sentimiento.
- Detección de velas japonesas y patrones.
- Clasificación de régimen de mercado.
- Gestión dinámica de exposición por operación.
- Regla de oro de riesgo: **nunca arriesgar más del 5% del capital total**.
- Frontend web para observabilidad y métricas.
- Documentación automática de planes operativos en Outline.

## Arquitectura del monorepo

- `apps/api`: API FastAPI + endpoints de salud, mercado, riesgo, métricas operativas y planes.
- `apps/worker`: motor de análisis/estrategias/riesgo y sincronización documental.
- `apps/web`: dashboard web en Next.js.
- `packages/shared`: contratos compartidos y documentación de payloads.
- `docs`: ADRs, diagramas, roadmap y especificaciones.
- `infra`: Docker, GitHub, despliegue y observabilidad.

## Estado actual

## Restricción de infraestructura

Todo el runtime productivo del proyecto debe desplegarse en el **NAS Synology** mediante contenedores. El servidor de OpenClaw **no** es un host válido para producción de este bot.

## Requisitos mínimos de runtime

- `apps/api`: Python 3.12 (Dockerfile basado en `python:3.12-slim`)
- `apps/worker`: **Python 3.11+** (actualmente desplegado con `python:3.12-slim`)
- `apps/web`: Node.js 22

El worker market-driven usa `asyncio.TaskGroup`; si se intenta ejecutar con Python < 3.11 debe fallar explícitamente al iniciar.

## Observabilidad baseline (PR-8)

- Endpoint API `GET /metrics` con métricas runtime (requests, errores, latencia, rutas, status codes).
- Protección opcional para `/metrics` vía header `x-metrics-key` cuando `metrics_api_key` está configurada.
- Logs estructurados JSON en API (`api_request`) y worker (`trade_plan_created`, `paper_trade_executed`, etc.).
- Política de fallos parciales del worker configurable con `strict_symbol_failures` (`STRICT_SYMBOL_FAILURES` en `.env`).

## Preflight + smoke + release gate Synology (PR-9/PR-10/PR-11)

Preflight de configuración (antes de levantar compose):

```bash
ENV_FILE=infra/docker/synology/.env \
./scripts/synology_preflight_check.sh
```

Si estás en un entorno sin Docker local, puedes ejecutar solo validación de variables:

```bash
ENV_FILE=infra/docker/synology/.env \
SKIP_COMPOSE_VALIDATION=true \
./scripts/synology_preflight_check.sh
```

Smoke funcional de endpoints:

```bash
API_BASE_URL="http://IP_NAS:API_PORT" \
WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
METRICS_API_KEY="<opcional>" \
./scripts/synology_smoke_test.sh
```

Release gate unificado (recomendado):

```bash
ENV_FILE=infra/docker/synology/.env \
API_BASE_URL="http://IP_NAS:API_PORT" \
WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
./scripts/synology_release_gate.sh
```

Atajo equivalente con Make:

```bash
make synology-release-gate \
  ENV_FILE=infra/docker/synology/.env \
  API_BASE_URL="http://IP_NAS:API_PORT" \
  WEB_BASE_URL="http://IP_NAS:WEB_PORT"
```

Ejecución remota desde GitHub Actions (`workflow_dispatch`):
- `Synology Preflight` (modo `require_secrets=true` usa `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `OUTLINE_API_TOKEN` desde GitHub Secrets)
- `Synology Smoke Test`
- `Synology Release Gate` (sube reporte Markdown + resumen JSON + checklist + paquete de sign-off, y valida estructura del JSON)
- `Synology Artifact Retention` (dry-run en CI para gobierno de artifacts operacionales)
- `Synology Observability & Alerting` (SLO + drift + health checks opcionales, con fallo explícito si hay alertas)
- `Synology Resilience Backup Verify` (evidencia diaria de backup/restore verificable para configuración crítica)
- Cierre formal de fase operativa documentado en `docs/plans/phase5-operational-closure.md`

Checklist de aprobación manual:

```bash
make synology-release-checklist CHECKLIST_PATH=artifacts/synology-release-checklist.md
```

Paquete consolidado de sign-off (gate + JSON + checklist):

```bash
make synology-signoff-package \
  REPORT_PATH=artifacts/synology-release-gate.md \
  JSON_PATH=artifacts/synology-release-gate.json \
  CHECKLIST_PATH=artifacts/synology-release-checklist.md \
  PACKAGE_PATH=artifacts/synology-signoff-package.md
```

Pipeline completo (recomendado en operación):

```bash
make synology-signoff-all \
  ENV_FILE=infra/docker/synology/.env \
  API_BASE_URL="http://IP_NAS:API_PORT" \
  WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
  SIGNOFF_OWNER="<responsable>"
```

Si Binance Testnet está intermitente y solo quieres validar salud interna del stack NAS, puedes correr:
`STRICT_EXTERNAL_CHECKS=false ./scripts/synology_smoke_test.sh`.

Este repositorio contiene la **fundación del proyecto**:

- blueprint de arquitectura
- ADRs iniciales
- motor base de riesgo
- agregador de señales
- clasificador de régimen
- cliente inicial de Outline
- API base
- dashboard base
- pipeline CI/CD inicial

## Regla de riesgo crítica

El sistema incorpora límites multicapa:

- riesgo por trade
- riesgo agregado simultáneo
- pérdida diaria
- pérdida semanal
- circuit breaker

> Ninguna estrategia puede saltarse el `RiskEngine`.

## Próximos hitos

1. Integración Binance Futures Testnet
2. Persistencia PostgreSQL + Alembic
3. Websockets de mercado
4. Backtesting / walk-forward con benchmark
5. Sincronización completa con Outline
6. Alertas y observabilidad avanzada

## Backtesting baseline (PR-33)

La API expone un backtest mínimo reproducible sobre candles persistidos en `market_candles`.

- Estrategia baseline: `ema_rsi_baseline` long-only.
- Benchmark: `buy_and_hold` del mismo activo y periodo.
- Walk-forward: ventanas de entrenamiento y prueba con selección explícita de parámetros.

Ejemplo:

```bash
curl -X POST "http://127.0.0.1:8000/backtesting/run" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "candles_limit": 600,
    "training_window": 200,
    "testing_window": 100,
    "initial_capital": 1000,
    "fee_rate": 0.0004
  }'
```

La respuesta incluye métricas del periodo completo y un resumen walk-forward con ventanas `in_sample` y `out_of_sample`.

## Documentación

Toda la documentación del proyecto está en español dentro de `docs/` y debe sincronizarse también en Outline.

- Índice local de estructura: `docs/README.md`
- Sync idempotente a Outline (evita duplicados por título y reescribe links locales a URLs navegables de Outline/GitHub):

```bash
OUTLINE_API_TOKEN="..." python3 scripts/sync_outline_docs.py
```

- Variables opcionales para la estrategia de links:
  - `OUTLINE_REPO_WEB_BASE` → fuerza la base web del repo (si no se detecta por `git remote`); puede ser la URL del repo o una URL `.../blob/<ref>`
  - `OUTLINE_GIT_REF` → ref usada para links `blob/<ref>` / fallback `raw` (default: `main`)

- Si se requiere limpieza de legacy docs no mapeados en el catálogo actual:

```bash
OUTLINE_API_TOKEN="..." python3 scripts/sync_outline_docs.py --archive-unknown
```

- Política de retención de artifacts operacionales:

```bash
make synology-artifact-retention KEEP_DAYS=45 RETENTION_DRY_RUN=true
```

- Observabilidad/alerting operacional del pipeline Synology:

```bash
GH_TOKEN="<github_token>" \
make synology-operational-observability \
  OPS_REPO=pantrux/binance-futures-algo-bot \
  OPS_WINDOW_HOURS=168 \
  OPS_MIN_SUCCESS_RATE=0.90
```

- Evidencia de resiliencia (backup/restore verificable):

```bash
make synology-resilience-backup \
  RESILIENCE_VERIFY_RESTORE=true \
  RESILIENCE_RTO_MINUTES=60 \
  RESILIENCE_RPO_MINUTES=1440
```

## Workflow GitHub

A partir de la fase actual, el proyecto opera con **branches + Pull Requests**.
La hoja de ruta formal de PRs está en `docs/pr-plan/PR_ROADMAP.md`.
