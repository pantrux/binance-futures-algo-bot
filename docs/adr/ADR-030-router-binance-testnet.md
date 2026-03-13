# ADR-030 — Router Binance Testnet y kill-switch operativo

## Estado
Aceptado

## Contexto
Tras PR-28 el sistema tiene gate final y circuit breakers, pero aún no ejecuta órdenes reales en exchange testnet desde un router dedicado con garantías de seguridad operacional.

## Objetivo de PR-29
- implementar `BinanceTestnetRouter` con API client encapsulado,
- aplicar kill-switch global y por símbolo antes de enviar órdenes,
- mantener modo paper como fallback explícito,
- auditar cada intento/envío/rechazo de orden con trazabilidad consistente.

## Decisión
Separar ejecución real en un módulo router específico y mantener el `TradePlanService` como productor de planes, no ejecutor directo.

## Implementación aprobada (PR-29)
1. `apps/worker/trading_bot/services/binance_testnet_router.py`:
   - preflight de ejecución por flags,
   - kill-switch global y por símbolo,
   - despacho a endpoint API de ejecución testnet.
2. `apps/api/app/services/testnet_trading_service.py`:
   - envío de orden `MARKET` a Binance Futures Testnet con firma,
   - persistencia de `Order`/`Position` y transición de `TradePlan` a `testnet_executed`,
   - manejo de errores con `RiskEvent` auditable.
3. Endpoints/API client:
   - `POST /testnet-trading/execute/{trade_plan_id}`,
   - `TradingBotApiClient.execute_testnet_trade(...)`.
4. Guardrails:
   - `testnet_execution_enabled` default `False` (deny-by-default),
   - fallback opcional a paper trading en worker (`testnet_fallback_to_paper`).
5. Tests unitarios/integración para router y servicio testnet.

## Consecuencias
### Positivas
- Separación clara entre planificación (`TradePlanService`) y ejecución (`BinanceTestnetRouter` + `BinanceTestnetTradingService`).
- Kill-switch explícito reduce riesgo de envíos accidentales en modo real.
- Persistencia de `Order`/`Position` y `RiskEvent` mejora trazabilidad operacional.

### Negativas
- Aumenta la superficie de integración (worker ↔ API ↔ Binance).
- Requiere mantenimiento continuo de compatibilidad con payloads/semántica de Binance Testnet.

### Neutrales
- El contrato de paper trading no cambia; permanece disponible como fallback.

## Riesgos
- Desalineación entre flags de seguridad y path de ejecución.
- Reintentos no controlados en escenarios de latencia/API errors.

## Mitigaciones
- defaults deny-by-default para ejecución real,
- idempotencia por client order id,
- logging estructurado por ciclo de decisión/ejecución,
- errores de credenciales con razón explícita (`testnet_credentials_missing`) y fallback controlado.
