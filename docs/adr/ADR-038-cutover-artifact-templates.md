# ADR-038: Templates operativos para artefactos de cutover

- **Estado:** Aceptado
- **Fecha:** 2026-03-14

## Contexto

Con `ADR-037` ya existe el contrato documental de drills y paquete de evidencia, pero aún faltan plantillas listas para uso operativo. Sin templates concretos, el operador puede improvisar nombres/campos y degradar la comparabilidad entre corridas.

## Decisión

Estandarizar templates operativos para:

- reporte inicial de cutover,
- reporte inicial en JSON máquina-legible,
- incident log,
- resultados de drills,
- cierre post-cutover.

Archivos fuente:

- `docs/templates/cutover-initial-report-template.md`
- `docs/templates/cutover-initial-report-template.json`
- `docs/templates/incident-log-template.md`
- `docs/templates/drill-results-template.md`
- `docs/templates/post-cutover-closeout-template.md`

## Consecuencias

### Positivas
- Menos improvisación en operación real.
- Artefactos homogéneos entre corridas.
- Handoff y auditoría más simples.

### Costos
- Requiere mantener las plantillas sincronizadas con los criterios vigentes.

## Alternativas consideradas

1. **Dejar ejemplos inline dentro del plan.** Rechazada: menos reutilizable y más difícil de copiar en operación real.
2. **Automatizar generación antes de fijar templates humanos.** Rechazada: primero conviene estabilizar el contrato manual.

## Referencias

- ADR-036: cutover controlado y monitoreo post-cutover
- ADR-037: drills sintéticos y paquete de evidencia de cutover
