# ADR-032 — Paridad paper vs testnet (shadow run)

## Estado
Aceptado

## Contexto
Con PR-29 (router testnet) y PR-30 (reconciliación) necesitamos una capa de comparación sistemática entre ejecuciones paper y testnet para detectar desvíos operativos sin esperar incidentes en producción.

## Decisión
Introducir servicios de parity/shadow run con reporte por símbolo, breakdown por `timeframe` y filtro opcional por `timeframe` para consumo operativo más fino:

- empareja trade plans `paper_executed` vs `testnet_executed` por lado (`long/short`),
- calcula diferencias porcentuales de:
  - `entry_price`,
  - `applied_risk_pct`,
  - `max_position_notional`,
- reporta pares comparados y ejecuciones no emparejadas.

## API
- `GET /execution/parity/{symbol}?timeframe=...&limit=...`

## Consecuencias
### Positivas
- visibilidad temprana de deriva entre modo paper y testnet.
- base para umbrales de alerta y smoke tests automáticos.

### Negativas
- incluso con `timeframe`, el emparejamiento por lado/orden temporal puede requerir refinamiento adicional para estrategias complejas multi-entrada dentro de una misma temporalidad.

### Neutrales
- no altera la ejecución; solo agrega observabilidad comparativa.
