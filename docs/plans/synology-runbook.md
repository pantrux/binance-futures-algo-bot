# Runbook Synology — arranque inicial y demo loop

## Objetivo
Levantar el stack completo en el NAS y poblar un conjunto mínimo de trade plans / paper executions para validar el circuito completo.

## Secuencia
1. Copiar repo al NAS.
2. Configurar `infra/docker/synology/.env`.
3. Ejecutar preflight de configuración:
   - `ENV_FILE=infra/docker/synology/.env ./scripts/synology_preflight_check.sh`
4. Ejecutar `docker compose up -d --build`.
5. Verificar que `migrate` termine OK.
6. Verificar `api` y `web` saludables.
7. Ejecutar seed/demo si se desea poblar datos:
   - `docker compose exec worker python /app/scripts/seed_demo_data.py`
8. Abrir el dashboard web y validar resumen + últimos trade plans.

## Verificaciones clave
- `/health`
- `/dashboard/summary`
- `/trade-plans`
- `/integrations/binance/testnet/ping`
- `/metrics` (con o sin `x-metrics-key`, según configuración)
- documentos en Outline creados por los trade plans

## Preflight automático (PR-10)

```bash
ENV_FILE=infra/docker/synology/.env \
./scripts/synology_preflight_check.sh
```

Opcional (modo estricto de secretos):

```bash
ENV_FILE=infra/docker/synology/.env \
REQUIRE_SECRETS=true \
./scripts/synology_preflight_check.sh
```

Opcional para entornos sin Docker local (solo validar `.env`):

```bash
ENV_FILE=infra/docker/synology/.env \
SKIP_COMPOSE_VALIDATION=true \
./scripts/synology_preflight_check.sh
```

También disponible por GitHub Actions (`Synology Preflight`, `workflow_dispatch`).

## Smoke test automático (PR-9)

Desde la raíz del repositorio:

```bash
API_BASE_URL="http://IP_NAS:API_PORT" \
WEB_BASE_URL="http://IP_NAS:WEB_PORT" \
METRICS_API_KEY="<opcional>" \
./scripts/synology_smoke_test.sh
```

### Criterio mínimo de aprobación
1. Todos los checks del script en verde.
2. `docker compose ps` sin servicios `unhealthy`.
3. Dashboard responde y muestra resumen sin errores 5xx.
4. API responde `testnet/ping` correctamente.
5. No activar live trading; mantener `PAPER_TRADING=true`.

> Nota operativa: `/integrations/binance/testnet/ping` depende de disponibilidad externa de Binance Testnet.
> Si Binance está intermitente, repetir el smoke o ejecutar temporalmente con `STRICT_EXTERNAL_CHECKS=false`
> para no bloquear validaciones internas del NAS por una caída externa puntual.
