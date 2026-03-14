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
10. Ejecutar validaciones remotas opcionales por GitHub Actions:
   - `Synology Preflight` (`workflow_dispatch`)
   - `Synology Smoke Test` (`workflow_dispatch`)
   - `Synology Release Gate` (`workflow_dispatch`)

## Prohibiciones
- No desplegar API/worker/web en OpenClaw.
- No almacenar claves de Binance en el repositorio.
- No activar live trading hasta completar paper trading y testnet.
