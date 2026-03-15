# Fase: ingesta inicial de mercado Binance

## Entregables
- tablas `market_candles` y `market_snapshots`
- migración Alembic
- servicio `BinanceMarketDataService`
- `POST /market/ingest/{symbol}`
- `GET /market/candles/{symbol}`
- `GET /market/snapshot/{symbol}`

## Alcance
Esta fase solo cubre la base de captura y lectura de mercado, no indicadores ni decisiones automáticas basadas en esos datos.

## Salida esperada
Tener el sistema listo para persistir OHLCV y snapshots, habilitando el siguiente PR de indicadores técnicos base.
