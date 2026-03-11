# ADR-019 — Checklist de sign-off operacional

## Estado
Aceptado (PR-15)

## Contexto
Tras PR-11/12/13/14 el gate técnico está sólido y automatizado (preflight + smoke + resumen JSON + verificación). Faltaba una pieza formal para aprobación humana trazable antes de considerar un ciclo operativo como “listo para operar en modo controlado”.

## Decisión
Agregar una checklist de sign-off operacional generable por script:

1. **Script** `scripts/synology_release_checklist.py`
   - genera plantilla Markdown con:
     - contexto de release
     - pasos de preflight/smoke/release/verify
     - bloque de aprobación final (responsable, fecha, observaciones)

2. **Target Make** `synology-release-checklist`
   - generación rápida y estandarizada del checklist

3. **Documentación**
   - README + runbook actualizados con uso del checklist

## Consecuencias
### Positivas
- Evidencia humana formal y consistente.
- Menor ambigüedad sobre “quién aprobó y cuándo”.
- Mejor auditoría de operación controlada.

### Trade-offs
- Añade un paso manual que requiere disciplina operativa.
- No sustituye validaciones automáticas; las complementa.

## Guardrail
- No habilita live trading.
- `PAPER_TRADING=true` sigue como condición obligatoria.
