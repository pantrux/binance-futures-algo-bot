# ADR-011 — Capa base de señales y features técnicos

## Estado
Aceptado

## Decisión
Construir una capa inicial de señales derivadas sobre los indicadores técnicos ya calculados on-demand.

## Features iniciales
- `trend_bias` basado en EMA(9) vs EMA(21)
- `momentum_bias` basado en RSI(14) + Momentum(10)
- `volatility_regime` basado en ATR% sobre EMA(21)
- `ema_spread_pct`
- `atr_pct`

## Justificación
Permite que el worker market-driven consuma una representación más semántica del mercado sin duplicar lógica de indicadores.

## Consecuencias
- se añade `SignalService`
- se expone endpoint `GET /signals/{symbol}`
- la fase siguiente puede usar estas señales como input de estrategias y scoring
