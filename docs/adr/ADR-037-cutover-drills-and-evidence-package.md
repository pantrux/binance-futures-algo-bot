# ADR-037: Drills sintéticos y paquete de evidencia de cutover

- **Estado:** Propuesto
- **Fecha:** 2026-03-14

## Contexto

El proyecto ya cuenta con:

- criterios formales de transición (`ADR-035`),
- runbook de cutover y monitoreo post-cutover (`ADR-036`),
- alerting y reporting operacional (`ADR-033`).

Sin embargo, todavía falta una capa explícita de **ensayo controlado** y una estructura uniforme de **evidencia de cutover**. Sin esa capa, un cutover real podría depender de memoria operativa, mensajes sueltos o evidencia incompleta.

## Decisión

Se agrega un plan específico de:

- drills sintéticos previos al cutover,
- paquete estándar de evidencia,
- criterio de aprobación/rechazo del ensayo.

Documento fuente:

- `docs/plans/cutover-drills-and-evidence-package.md`

## Consecuencias

### Positivas
- Hace el cutover **ensayable** antes de tocar exposición real.
- Reduce improvisación ante incidentes.
- Deja evidencia consistente para auditoría y handoff.

### Costos
- Agrega fricción operativa deliberada.
- Requiere mantener artefactos y enlaces en Outline.

## Alternativas consideradas

1. **Dejar drills como tarea informal del operador.** Rechazada: demasiado dependiente de memoria humana.
2. **Automatizar todo el paquete desde CI antes de definir el contrato documental.** Rechazada por prematura; primero conviene fijar el contrato operativo.

## Referencias

- ADR-033: production alerting and daily reporting
- ADR-035: checklist transición y rampa de capital
- ADR-036: cutover controlado y monitoreo post-cutover
