# ADR-013 — Gate de smoke tests para despliegue Synology

## Estado
Aceptado (PR-9)

## Contexto
Con PR-8 se completó la base de observabilidad, pero faltaba un gate operativo repetible para validar que el despliegue en Synology está sano antes de avanzar de paper/testnet.

Hasta ahora, las validaciones eran mayormente manuales y no estaban estandarizadas en un script único ni en un workflow de GitHub reproducible.

## Decisión
Definir un gate de validación mínima para despliegue real en Synology compuesto por:

1. **Script de smoke tests local/remoto** (`scripts/synology_smoke_test.sh`)
   - verifica endpoints:
     - `/health`
     - `/dashboard/summary`
     - `/trade-plans`
     - `/integrations/binance/testnet/ping`
     - `/metrics` (con o sin `x-metrics-key`)
   - verifica respuesta base de web (`Trading Bot`)

2. **Workflow manual de GitHub** (`.github/workflows/synology-smoke.yml`)
   - `workflow_dispatch`
   - inputs de `api_base_url` y `web_base_url`
   - uso opcional de `secrets.METRICS_API_KEY`

3. **Runbook actualizado**
   - `docs/plans/synology-runbook.md`
   - `docs/plans/synology-deployment.md`

## Consecuencias
### Positivas
- Validación operativa reproducible y auditable antes de cambios de fase.
- Menor dependencia de verificaciones ad-hoc.
- Mejor trazabilidad para incidentes de despliegue.

### Trade-offs
- El smoke test valida salud funcional básica, no performance ni resiliencia avanzada.
- Requiere mantener URLs/base paths correctos en entornos NAS/proxy.

## Guardrail permanente
- No habilitar live trading en este gate.
- Mantener `PAPER_TRADING=true` hasta completar validaciones adicionales de operación controlada.
