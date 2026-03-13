# ADR-033 — Alerting y reporting de producción

## Estado
Aceptado

## Contexto
Con PR-31 ya existe paridad paper/testnet y reconciliación de ejecución, pero faltaba una capa compacta para monitoreo operacional diario y disparo de alertas tempranas.

## Decisión
Agregar `ProductionReportingService` con dos salidas:

1. `daily_summary()`
   - KPIs de volumen y estado de trade plans,
   - score promedio,
   - conteo de eventos críticos/warning últimas 24h.

2. `evaluate_alerts()`
   - reglas iniciales de alerta:
     - picos de eventos críticos,
     - conversión aprobados/bloqueados,
     - ausencia de ejecución testnet con presencia de paper,
     - degradación de calidad de score.

## API
- `GET /reporting/daily-summary`
- `GET /alerts/evaluate`

## Consecuencias
### Positivas
- visibilidad operativa rápida para revisión diaria.
- base simple para integraciones futuras (Telegram/email/webhooks).

### Negativas
- reglas heurísticas iniciales pueden requerir ajuste por régimen/mercado.

### Neutrales
- no altera decisión de trading; solo añade observabilidad y alerting.
