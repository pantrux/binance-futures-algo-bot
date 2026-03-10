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

## Secuencia de despliegue
1. Copiar repositorio al NAS.
2. Copiar `infra/docker/synology/.env.example` a `.env`.
3. Ajustar credenciales y puertos.
4. Ejecutar `docker compose up -d --build` desde `infra/docker/synology`.
5. Validar salud de `postgres`, `redis`, `api`, `worker` y `web`.
6. Configurar reverse proxy del NAS o Nginx Proxy Manager.

## Prohibiciones
- No desplegar API/worker/web en OpenClaw.
- No almacenar claves de Binance en el repositorio.
- No activar live trading hasta completar paper trading y testnet.
