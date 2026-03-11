# Flujo worker híbrido (market→demo)

```mermaid
flowchart TD
    A[Worker híbrido] --> B[GET /signals/{symbol}]
    B -->|OK (data suficiente)| C[Construir SignalPack+MarketContext]
    B -->|404/400/error| D[Fallback DemoSignalService]
    C --> E[POST /trade-plans]
    D --> E
    E --> F[Persistencia + Outline]
    F --> G{approved?}
    G -- Sí --> H[POST /paper-trading/execute/{id}]
    H --> I[orders + positions]
    G -- No --> J[risk_events]
    I --> K[Dashboard /trade-plans y /dashboard/summary]
```
