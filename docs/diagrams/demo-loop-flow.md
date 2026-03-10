# Flujo demo loop

```mermaid
flowchart TD
    A[Worker demo] --> B[DemoSignalService]
    B --> C[POST /trade-plans]
    C --> D[Persistencia + Outline]
    D --> E{approved?}
    E -- Sí --> F[POST /paper-trading/execute/{id}]
    F --> G[orders + positions]
    E -- No --> H[risk_events]
    G --> I[Dashboard /trade-plans y /dashboard/summary]
```
