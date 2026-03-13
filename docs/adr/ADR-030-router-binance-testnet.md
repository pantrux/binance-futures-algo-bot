# ADR-030 — Router Binance Testnet y kill-switch operativo

## Estado
Propuesto

## Contexto
Tras PR-28 el sistema tiene gate final y circuit breakers, pero aún no ejecuta órdenes reales en exchange testnet desde un router dedicado con garantías de seguridad operacional.

## Objetivo de PR-29
- implementar `BinanceTestnetRouter` con API client encapsulado,
- aplicar kill-switch global y por símbolo antes de enviar órdenes,
- mantener modo paper como fallback explícito,
- auditar cada intento/envío/rechazo de orden con trazabilidad consistente.

## Decisión preliminar
Separar ejecución real en un módulo router específico y mantener el `TradePlanService` como productor de planes, no ejecutor directo.

## Entregables previstos
1. Servicio `binance_testnet_router.py` en worker.
2. Verificaciones de preflight (credenciales, conectividad, flags de seguridad).
3. Kill-switch operativo (global + por símbolo + por breaker crítico).
4. Tests unitarios/integración de rutas de envío y bloqueo.

## Riesgos
- Desalineación entre flags de seguridad y path de ejecución.
- Reintentos no controlados en escenarios de latencia/API errors.

## Mitigaciones
- defaults deny-by-default para ejecución real,
- idempotencia por client order id,
- logging estructurado por ciclo de decisión/ejecución.
