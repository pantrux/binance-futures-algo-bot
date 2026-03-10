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
- documentos en Outline creados por los trade plans
