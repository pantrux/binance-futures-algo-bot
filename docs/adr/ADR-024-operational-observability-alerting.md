# ADR-024 — Observabilidad y alerting operacional de infraestructura

- **Estado:** Aprobada
- **Fecha:** 2026-03-12
- **PR:** PR-23

## Contexto

Con `PR-22` quedó resuelta la retención de artifacts operacionales, pero aún faltaba una capa explícita de observabilidad para detectar tempranamente:

1. degradación del pipeline de operación (`preflight`, `smoke`, `release gate`, `artifact retention`),
2. ausencia de corridas esperadas (drift operativo),
3. degradación de health endpoints cuando se configuren URLs públicas.

Necesitamos un mecanismo auditable y automatizable que entregue una señal clara (`OK`/`ALERT`) y evidencia serializable (`JSON + Markdown`).

## Decisión

Se implementa un módulo dedicado de observabilidad operacional:

- Script: `scripts/synology_operational_observability.py`
  - consulta runs de workflows vía GitHub API,
  - calcula métricas/SLO por workflow en una ventana configurable,
  - evalúa drift operativo por mínimo de corridas,
  - ejecuta health checks opcionales,
  - genera artefactos:
    - `artifacts/synology-operational-observability.json`
    - `artifacts/synology-operational-observability.md`
  - retorna `exit 1` cuando detecta alertas.

- Workflow: `.github/workflows/synology-observability-alerting.yml`
  - ejecución por `schedule` (horaria) y `workflow_dispatch`,
  - publica resumen en `GITHUB_STEP_SUMMARY`,
  - sube artifacts siempre,
  - falla el job cuando hay alertas (señal operativa explícita).

- Make target:
  - `make synology-operational-observability`
  - permite ejecución local/manual en Synology con parámetros de ventana/SLO/health.

## Consecuencias

### Positivas

- El estado operativo deja de depender de inspección manual de runs dispersos.
- Se puede auditar continuidad de operación con evidencia estructurada.
- Fallos parciales quedan convertidos en señal de pipeline y no solo en logs.

### Trade-offs

- El cálculo de SLO depende de disponibilidad de GitHub API.
- Los health checks en workflow dependen de URLs alcanzables desde GitHub-hosted runners.
  - Por diseño, se permiten checks opcionales vía `vars.SYNOLOGY_HEALTH_API_URL` / `vars.SYNOLOGY_HEALTH_WEB_URL`.

## Guardrails

- No habilita live trading ni altera lógica de ejecución de órdenes.
- Mantiene `PAPER_TRADING=true` como postura operativa segura.
- Cualquier alerta exige revisión antes de considerar la operación como saludable.
