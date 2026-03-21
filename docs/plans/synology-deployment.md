# Despliegue objetivo en Synology NAS

## Regla operativa
Toda la infraestructura del proyecto debe ejecutarse en contenedores dentro del NAS Synology. El servidor OpenClaw no debe hospedar runtime productivo del bot.

## Servicios contenedorizados
- `trading-bot-postgres`
- `trading-bot-redis`
- `trading-bot-api`
- `trading-bot-worker`
- `trading-bot-web`

## Rutas sugeridas en el NAS
- Proyecto: `/volume1/docker/binance-futures-algo-bot`
- Datos PostgreSQL: `/volume1/docker/binance-futures-algo-bot/postgres`
- Datos Redis: `/volume1/docker/binance-futures-algo-bot/redis`

## Variables críticas
- `OUTLINE_API_URL`
- `OUTLINE_API_TOKEN`
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`
- `MAX_ACCOUNT_RISK_PCT=5`
- `PAPER_TRADING=true`
- `OPERATIONAL_CUTOVER_AT=<ISO-8601 con timezone>` cuando quieras iniciar una nueva era operativa limpia en dashboard/shadow run

> Validación real post `PR-41`: si `BINANCE_API_KEY` / `BINANCE_API_SECRET` están vacíos, Synology solo producirá `paper_executed` y el Gate C de shadow run fallará por ausencia total de ejecuciones testnet.

## Secuencia de despliegue
1. Copiar repositorio al NAS.
2. Copiar `infra/docker/synology/.env.example` a `.env`.
3. Ajustar credenciales y puertos.
4. Ejecutar preflight:
   - `ENV_FILE=infra/docker/synology/.env ./scripts/synology_preflight_check.sh`
5. Ejecutar `docker compose up -d --build` desde `infra/docker/synology`.
6. Validar salud de `postgres`, `redis`, `api`, `worker` y `web`.
7. Ejecutar smoke test:
   - `API_BASE_URL=... WEB_BASE_URL=... ./scripts/synology_smoke_test.sh`
8. Configurar reverse proxy del NAS o Nginx Proxy Manager.
9. Ejecutar release gate unificado (recomendado):
   - `ENV_FILE=... API_BASE_URL=... WEB_BASE_URL=... ./scripts/synology_release_gate.sh`
10. Registrar evidencia del despliegue usando `docs/templates/synology-deploy-evidence-template.md`.
11. Ejecutar validaciones remotas opcionales por GitHub Actions:
   - `Synology Preflight` (`workflow_dispatch`)
   - `Synology Smoke Test` (`workflow_dispatch`)
   - `Synology Release Gate` (`workflow_dispatch`)
   - `Outline Docs Sync` (`workflow_dispatch`, cuando el despliegue implique cambios documentales relevantes)

## Mapa operativo de URLs
- `http://api:8000` → tráfico interno entre contenedores Docker (`worker`, SSR del `web`, validaciones internas del stack).
- `NEXT_PUBLIC_API_URL` → URL pública accesible desde el navegador del operador (por IP LAN o dominio/reverse proxy del NAS).
- `API_BASE_URL` en smoke/release gate → endpoint público que debe representar la API real expuesta por el NAS.
- `WEB_BASE_URL` en smoke/release gate → endpoint público real de la UI expuesta por el NAS.

## Worker one-shot
- `trading-bot-worker` está diseñado para correr como job one-shot y quedar en `Exited (0)` cuando termina correctamente.
- Ese estado no implica falla; implica que el ciclo de trabajo concluyó según diseño.
- Si necesitas reejecutarlo en el NAS, usar una corrida explícita controlada (`docker compose up worker` o equivalente documentado por tu operación actual).
- Después de reejecutarlo, revisar logs del contenedor y validar efectos en API/UI antes de asumir éxito.

## Runtime near real-time (habilitado por config)
- El worker ahora soporta `RUNTIME_MODE=loop` para operar como loop persistente con polling controlado.
- En `oneshot`, se mantiene el comportamiento histórico y se usa `DEFAULT_SIGNAL_TIMEFRAME`.
- En `oneshot`, el estado sano esperado del contenedor sigue siendo `Exited (0)`; en `loop`, el estado sano esperado es `Up`.
- En `loop`, el worker evalúa `TIMEFRAMES` y evita duplicar decisiones dentro de la misma vela por `(symbol, timeframe, last_candle_close_ms)`.
- Variables nuevas:
  - `RUNTIME_MODE=oneshot|loop`
  - `POLL_INTERVAL_SECONDS=30`
  - `MAX_CYCLES=0` (`0` = infinito)
  - usar `MAX_CYCLES>0` solo para pruebas controladas
  - `TIMEFRAMES=5m,15m,1h`
  - `DEFAULT_SIGNAL_TIMEFRAME=15m`

## Evidencia mínima recomendada por despliegue
- `git rev-parse --short HEAD`
- `docker compose ps`
- `docker compose images`
- resultado de preflight/smoke/release gate
- evidencia de sync a Outline si hubo cambios documentales u operativos relevantes

## Prohibiciones
- No desplegar API/worker/web en OpenClaw.
- No almacenar claves de Binance en el repositorio.
- No activar live trading hasta completar paper trading y testnet.
AD`
- `docker compose ps`
- `docker compose images`
- resultado de preflight/smoke/release gate
- evidencia de sync a Outline si hubo cambios documentales u operativos relevantes
- `OPERATIONAL_CUTOVER_AT` aplicado si el despliegue inaugura nueva era operativa

## Prohibiciones
- No desplegar API/worker/web en OpenClaw.
- No almacenar claves de Binance en el repositorio.
- No activar live trading hasta completar paper trading y testnet.
