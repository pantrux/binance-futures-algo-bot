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
- el valor de RSI depende de la ventana (`limit`) usada para cargar candles; en esta fase se acepta como snapshot on-demand y se deja documentado para consumidores del API
- no se persisten todavía los indicadores (fase posterior)
