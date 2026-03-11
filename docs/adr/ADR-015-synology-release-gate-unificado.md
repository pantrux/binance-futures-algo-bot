# ADR-015 — Release gate unificado para Synology

## Estado
Aceptado (PR-11)

## Contexto
Después de PR-9 (smoke) y PR-10 (preflight), las validaciones existían pero separadas. Esto elevaba la fricción operativa y hacía más difícil auditar una corrida completa de gate antes de avanzar en operación controlada.

## Decisión
Unificar el gate operativo en una sola ejecución:

1. **Script `scripts/synology_release_gate.sh`**
   - ejecuta `preflight` y luego `smoke`
   - genera reporte Markdown consolidado con logs por etapa
   - falla el proceso si cualquiera de las etapas falla

2. **Workflow manual `Synology Release Gate`**
   - `workflow_dispatch`
   - inputs para URLs de API/Web y flags de strictness
   - sube artifact `synology-release-gate-report`

3. **Runbook actualizado**
   - secuencia recomendada: `release_gate` como validación principal
   - preflight/smoke individuales quedan disponibles para debugging puntual

## Consecuencias
### Positivas
- Menor fricción operativa (un solo comando/workflow).
- Evidencia auditable de gate por corrida.
- Menor riesgo de “pasos omitidos” entre preflight y smoke.

### Trade-offs
- Script más largo y con mayor superficie de mantenimiento.
- Dependencia de correcta provisión de variables/URLs en el workflow manual.

## Guardrail
- Sin live trading en este gate.
- `PAPER_TRADING=true` sigue obligatorio hasta cierre formal de operación controlada.
