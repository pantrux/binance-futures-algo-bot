# ADR-036: Cutover controlado y monitoreo post-cutover

- **Estado:** Propuesto
- **Fecha:** 2026-03-14

## Contexto

El sistema requiere una transición controlada (paper→testnet→real) y, una vez en el entorno objetivo, necesita un periodo de observación con métricas y alertas reforzadas. Sin un runbook explícito se incrementa el riesgo de:

- cambios “rápidos” sin freeze window,
- falta de validación inmediata,
- rollback tardío,
- ausencia de evidencia post-incidente.

## Decisión

Se documenta un runbook de **cutover controlado** y un set mínimo de **monitoreo post-cutover**, en:

- `docs/plans/cutover-and-post-cutover-monitoring.md`

Este documento será el procedimiento estándar para cada cutover y para el periodo post-cutover.

## Consecuencias

### Positivas
- Reduce riesgo operacional y acelera el triage.
- Hace el rollback repetible (menos improvisación).
- Define una secuencia única de acciones (pre-flight → cutover → validación → observación).

### Costos
- Agrega fricción deliberada (freeze window, evidencias, checkpoints).

## Alternativas consideradas

1. **Cutover ad-hoc por mensajes.** Rechazada: no repetible y propensa a errores.
2. **Automatizar cutover completo.** Posible a futuro, pero requiere historia operativa y controles adicionales.

## Referencias

- ADR-035: checklist transición y rampa de capital
