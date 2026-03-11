# Runbook Synology — arranque inicial y demo loop

## Objetivo
Levantar el stack completo en el NAS y poblar un conjunto mínimo de trade plans / paper executions para validar el circuito completo.

## Secuencia
1. Copiar repo al NAS.
2. Configurar `infra/docker/synology/.env`.
3. Ejecutar `docker compose up -d --build`.
4. Verificar que `migrate` termine OK.
5. Verificar `api` y `web` saludables.
6. Ejecutar seed/demo si se desea poblar datos:
   - `docker compose exec worker python /app/scripts/seed_demo_data.py`
7. Abrir el dashboard web y validar resumen + últimos trade plans.

## Verificaciones clave
- `/health`
- `/dashboard/summary`
- `/trade-plans`
- `/integrations/binance/testnet/ping`
- `/metrics` (con o sin `x-metrics-key`, según configuración)
- documentos en Outline creados por los trade plans

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
