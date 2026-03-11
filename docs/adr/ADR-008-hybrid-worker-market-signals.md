# ADR-008: Worker híbrido (market-driven con fallback a demo)

- **Fecha:** 2026-03-10
- **Estado:** Aceptado (corte mínimo PR-7)

## Contexto

Hasta ahora el `apps/worker` construía un `TradePlanCreateRequest` usando un `DemoSignalService` con presets hardcodeados.

Ya existe un endpoint en el API:

- `GET /signals/{symbol}?timeframe=15m&limit=200`

que devuelve un `SignalSnapshot` basado en candles/indicadores persistidos. Ese endpoint devuelve:

- **404** si no hay candles
- **400** si hay candles pero no suficientes para indicadores/señales

## Decisión

Implementar un **worker híbrido** que:

1) **Intenta** consumir `GET /signals/{symbol}` y `GET /market/snapshot/{symbol}`.
2) Si el snapshot es usable (no `unknown`, sin `None` críticos), construye:
   - `SignalPack` (technical/fundamental/sentiment/confidence)
   - `MarketContext` (volatility_pct/trend_strength/liquidity_score)
   - Niveles (entry/stop/take_profit) **basados en ATR%** y precio de mercado.
   - **Contrato explícito:**
     - `atr_pct` llega desde `/signals/{symbol}` como porcentaje real (`ATR / EMA * 100`), por lo que el worker lo convierte siempre a fracción decimal dividiendo por `100` antes de calcular niveles y penalizaciones.
     - `ema_spread_pct` también llega como porcentaje real (`(EMA9 - EMA21) / EMA21 * 100`); `trend_strength` trabaja sobre ese formato sin convertirlo a fracción.
3) Si falla la API o no hay data suficiente, hace **fallback controlado** a `DemoSignalService`.

## Consecuencias

- El worker deja de depender exclusivamente de valores demo y puede operar cuando el pipeline de market ingestion ya alimentó la DB.
- La conversión `SignalSnapshot (bias/regime/features) -> SignalPack (scores)` es **heurística** (intencionalmente simple) para este corte mínimo.

## Alternativas consideradas

- Esperar a que el API exponga un endpoint directamente compatible con `SignalPack` y `MarketContext`.
- Mover toda la generación de niveles/thesis al API.

## Implementación

- Nuevo servicio: `apps/worker/trading_bot/services/hybrid_signal_service.py`
- Cambios:
  - `apps/worker/main.py`: usa `HybridSignalService`
  - `apps/worker/trading_bot/services/api_client.py`: agrega `get_signal_snapshot` y `get_market_snapshot`

## Requisitos de runtime

- El worker requiere **Python 3.11+** porque usa `asyncio.TaskGroup`.
- En el runtime productivo Synology esto queda cubierto por las imágenes Docker basadas en `python:3.12-slim`.
- Si se intenta ejecutar el worker con Python < 3.11, debe fallar explícitamente al arranque en lugar de degradar silenciosamente al path demo.

## Testing

- Tests unitarios mínimos verifican:
  - uso de market cuando hay snapshot usable
  - fallback a demo cuando la API falla
