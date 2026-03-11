# ADR-008 — Fundación de ingesta de mercado Binance

## Estado
Aceptado

## Decisión
Incorporar una capa inicial de ingesta de mercado para Binance Futures basada en:
- candles OHLCV
- snapshot de precios/mark/index
- open interest
- funding rate
- volumen 24h

## Justificación
El worker necesita dejar de operar solo con presets estáticos y comenzar a apoyarse en datos reales de mercado.

## Consecuencias
- Se crean tablas `market_candles` y `market_snapshots`.
- La API expone endpoints de ingestión y lectura.
- El siguiente PR puede construir indicadores técnicos sobre esta base persistente.
