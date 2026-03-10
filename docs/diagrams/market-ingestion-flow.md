# Flujo de ingesta de mercado

```mermaid
flowchart TD
    A[Binance Futures API] --> B[BinanceMarketDataService]
    B --> C[Persistir market_candles]
    B --> D[Persistir market_snapshots]
    C --> E[GET /market/candles/{symbol}]
    D --> F[GET /market/snapshot/{symbol}]
    C --> G[PR siguiente: indicadores técnicos]
```
