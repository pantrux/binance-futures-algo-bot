# ADR-034: backtesting y walk-forward mínimos con benchmark

## Estado
Aprobado

## Contexto
La plataforma ya dispone de ingesta de `market_candles`, indicadores, señales, régimen, riesgo, paper trading, testnet y reporting. Faltaba una capa cuantitativa mínima para validar una estrategia de referencia con métricas reproducibles antes de avanzar en la etapa de preparación para salida controlada.

El objetivo de `PR-33` no es construir un motor de research genérico, sino una primera versión auditable que:

- reutilice candles persistidos en la base;
- exponga resultados por API con el mismo estilo del proyecto;
- compare estrategia vs benchmark;
- separe dentro de muestra y fuera de muestra mediante walk-forward simple.

## Decisión
Se incorpora un servicio `BacktestingService` con las siguientes decisiones explícitas:

1. La fuente de datos es exclusivamente `market_candles` persistido en la base.
   El scope operacional permitido para backtesting queda limitado a `BTCUSDT`, `ETHUSDT` y `SOLUSDT`.
2. La estrategia baseline es `ema_rsi_baseline`, solo posiciones largas, con cruce EMA rápido/lento y filtro RSI.
3. El benchmark es `buy_and_hold` del mismo activo, mismo timeframe y mismo periodo.
4. El walk-forward usa ventanas deslizantes simples de entrenamiento/prueba.
5. La selección de parámetros dentro de muestra se limita a una grilla corta y explícita de configuraciones baseline para priorizar auditabilidad.
6. Las métricas mínimas obligatorias son:
   - `total_return_pct`
   - `win_rate_pct`
   - `profit_factor`
   - `max_drawdown_pct`
   - `trades_count`
   - `ending_capital`
7. El punto de acceso oficial es `POST /backtesting/run`.

## Consecuencias

### Positivas
- El proyecto gana una base cuantitativa reproducible sin dependencias pesadas adicionales.
- La comparación estrategia vs benchmark queda normalizada dentro de la API.
- El walk-forward deja evidencia explícita de robustez dentro y fuera de muestra.

### Negativas
- La simulación actual es deliberadamente simple: solo posiciones largas, sin deslizamiento, sin financiamiento y sin apalancamiento.
- La optimización de parámetros no es exhaustiva y solo cubre una grilla pequeña.
- El benchmark inicial es únicamente comprar y mantener del mismo activo.

## Follow-up natural
- agregar deslizamiento y costos más cercanos a Binance Futures;
- soportar estrategias cortas o largo/corto;
- guardar corridas y reportes en persistencia si la operación lo requiere;
- exponer filtros adicionales por rango temporal y no solo por `candles_limit`.
