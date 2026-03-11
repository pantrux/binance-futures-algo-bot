# ADR-018 — Estandarización operativa con Makefile

## Estado
Aceptado (PR-14)

## Contexto
El flujo operativo Synology ya incluye múltiples scripts (`preflight`, `smoke`, `release_gate`, `summary`, `verify`). Aunque funcionales, su invocación directa requiere comandos largos y repetitivos, aumentando fricción y riesgo de error humano.

## Decisión
Agregar un `Makefile` en la raíz del repo con targets operativos estándar:
- `synology-preflight`
- `synology-smoke`
- `synology-release-gate`
- `synology-release-summary`
- `synology-release-verify`

Los targets aceptan variables de entorno (`ENV_FILE`, `API_BASE_URL`, `WEB_BASE_URL`, etc.) para mantener flexibilidad sin sacrificar ergonomía.

## Consecuencias
### Positivas
- Menor fricción para operación diaria.
- Menor probabilidad de errores por comandos manuales largos.
- Flujo más repetible para on-call/debug.

### Trade-offs
- Se introduce otra capa de abstracción que requiere mantenimiento.
- Debe mantenerse sincronizado con flags y scripts subyacentes.

## Guardrail
- No modifica política de trading.
- `PAPER_TRADING=true` sigue obligatorio en operación controlada.
