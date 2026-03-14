# ADR-035: Checklist de transición y rampa de capital

- **Estado:** Propuesto
- **Fecha:** 2026-03-14

## Contexto

El proyecto opera bajo el principio **paper → testnet → real** con guardrails estrictos. Hasta ahora existían piezas aisladas (release gates, observabilidad, paridad paper/testnet, backtesting), pero no había un documento único que definiera:

- condiciones **go/no-go** por etapa;
- evidencia mínima requerida;
- política de rampa de capital;
- plan de rollback.

## Decisión

Se introduce una **checklist de transición** y una **política de rampa de capital por etapas** como fuente de verdad, documentadas en:

- `docs/plans/transition-checklist-and-capital-ramp.md`

La checklist será obligatoria antes de cualquier transición fuera de paper o testnet.

## Consecuencias

### Positivas

- Reduce ambigüedad operacional y decisiones impulsivas.
- Incrementa auditabilidad: cada transición queda respaldada por evidencia.
- Facilita iteración: se pueden ajustar umbrales por estrategia sin romper el flujo.

### Costos

- Requiere mantener umbrales y evidencias actualizadas.
- Puede aumentar fricción para iterar rápido, pero es intencional para evitar riesgo.

## Alternativas consideradas

1. **Transición ad-hoc con runbook.** Rechazada: alta probabilidad de drift y falta de trazabilidad.
2. **Automatizar toda la decisión de transición.** Rechazada por ahora: requiere más historia de datos y controles robustos; se puede implementar luego.

## Referencias

- ADR-006: paper trading first
- ADR-032: paridad paper vs testnet
- ADR-033: reporting/alerting
- ADR-034: backtesting/walk-forward
