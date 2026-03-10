# ADR-009 — Hardening de la ingesta de mercado

## Estado
Aceptado

## Decisión
Corregir la capa inicial de ingesta de mercado para que soporte timestamps de Binance en milisegundos y garantice consistencia de sesión/transacción ante errores.

## Cambios clave
- `open_time_ms` y `close_time_ms` pasan a `BigInteger`
- constraint único compuesto en `market_candles`
- rollback explícito ante errores HTTP/parseo/DB
- llamadas HTTP en paralelo con `asyncio.gather`

## Justificación
La versión inicial era funcional pero tenía riesgo real de overflow y de dejar la sesión SQLAlchemy en estado inválido.
