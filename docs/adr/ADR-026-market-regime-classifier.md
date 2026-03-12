# ADR-026: Clasificador de régimen de mercado (Market Regime)

## Estado
✅ Aprobado (implementación inicial)

## Contexto
El bot ya cuenta con:
- Ingesta de mercado (candles)
- Indicadores técnicos base
- Señales/features derivados (trend/momentum/volatilidad)

Para el siguiente bloque de decisiones de riesgo (Fase 7+) necesitamos un **contexto compacto** que sintetice el “estado del mercado” y sea consumible por:
- `RiskEngine` (gates y degradación de exposición)
- `TradePlanService` / worker (decisión final)
- Observabilidad (dashboards y auditoría)

## Decisión
Implementar un **Market Regime Classifier** determinístico (sin ML por ahora) que produzca un `MarketRegimeSnapshot` por símbolo/timeframe basado en:
- `trend_bias`, `momentum_bias`, `volatility_regime`
- métricas cuantitativas simples normalizadas a score (0..100):
  - `trend_strength` (derivado de `ema_spread_pct`)
  - `volatility_score` (derivado de `atr_pct`)
  - `momentum_score` (derivado de `rsi_14` + `momentum_10`)

Salida principal: `regime` ∈ {`tendencia_alcista`, `tendencia_bajista`, `rango_lateral`, `transicion`, `alta_volatilidad`, `unknown`} + `regime_confidence` (0..100).

## Alcance inicial
- Implementación en API como servicio (`MarketRegimeService`) y schema (`MarketRegimeSnapshot`).
- Endpoint `GET /market/regime/{symbol}` para inspección y consumo por otros componentes.

## Consecuencias
- El régimen queda **auditado y estable** (misma entrada → misma salida), útil para debugging y gates.
- No se agrega dependencia externa ni complejidad de entrenamiento.
- La heurística se podrá endurecer en PRs posteriores (PR-26+), y el `RiskEngine` podrá usar `regime/regime_confidence` como feature de gating.

## Follow-ups
- Integrar régimen en `RiskEngine` como guardrail (por ejemplo: degradar sizing en `alta_volatilidad` y `transicion`).
- Persistir snapshots (opcional) si queremos series de régimen por símbolo.
