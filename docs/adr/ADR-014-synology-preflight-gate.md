# ADR-014 — Gate de preflight para despliegue Synology

## Estado
Aceptado (PR-10)

## Contexto
Con PR-9 se incorporó el smoke test funcional post-despliegue. Sin embargo, seguía faltando una validación previa al `docker compose up` para detectar configuración incompleta (`.env`) y errores de resolución de compose antes de gastar tiempo en builds y arranques.

## Decisión
Agregar un gate de preflight reproducible para Synology:

1. **Script `scripts/synology_preflight_check.sh`**
   - valida existencia de `.env`
   - valida variables mínimas requeridas
   - valida `docker compose config -q`
   - soporte opcional de modo estricto (`REQUIRE_SECRETS=true`)
   - soporte opcional de creación de directorios de datos (`AUTO_CREATE_DATA_DIRS=true`)

2. **Workflow manual `Synology Preflight`**
   - `workflow_dispatch`
   - ejecuta preflight sobre `.env.example` (validación estructural)

3. **Documentación de operación**
   - runbook y guía de despliegue actualizados para exigir preflight antes del smoke

## Consecuencias
### Positivas
- Falla temprano por configuración incompleta.
- Reduce ciclos de debugging tardío en NAS.
- Complementa al smoke test: preflight (config) + smoke (funcionalidad).

### Trade-offs
- El preflight no valida conectividad real contra servicios externos ni credenciales reales (eso se cubre en despliegue/smoke reales).
- Modo estricto de secretos debe habilitarse explícitamente para entornos productivos.
- El script carga `ENV_FILE` con `source`, por lo que el archivo debe ser de confianza (operador/controlado).

## Guardrail
- Este gate no autoriza live trading.
- `PAPER_TRADING=true` se mantiene como condición obligatoria hasta cierre de operación controlada.
