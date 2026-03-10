# Fase: expansión del dominio operativo

## Entregables
- tablas `orders`, `positions`, `risk_events`
- migración Alembic de dominio operativo
- `PaperTradingService`
- `POST /paper-trading/execute/{trade_plan_id}`
- `GET /dashboard/summary`
- `GET /trade-plans`
- dashboard web leyendo resumen y últimos trade plans

## Objetivo
Construir el esqueleto transaccional necesario para simular ejecuciones, abrir posiciones virtuales y empezar a medir salud operativa.
