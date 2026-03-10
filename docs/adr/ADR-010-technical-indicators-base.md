# ADR-010 — Capa base de indicadores técnicos

## Estado
Aceptado

## Decisión
Introducir una capa inicial de indicadores calculados sobre `market_candles` persistidos:
- EMA(9)
- EMA(21)
- RSI(14)
- ATR(14)
- Momentum(10)

## Justificación
Permite pasar de ingesta de mercado a señales técnicas reproducibles para el worker market-driven.

## Consecuencias
- se añade `IndicatorService`
- se expone endpoint `GET /indicators/{symbol}`
- no se persisten todavía los indicadores (fase posterior)
