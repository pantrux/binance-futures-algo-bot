# ADR-020 — Consolidación del paquete de sign-off operacional

## Estado
Aceptado (PR-16)

## Contexto
Con PR-15 existe checklist manual, pero la evidencia de cierre operativo sigue dispersa en múltiples archivos (`release-gate.md`, `release-gate.json`, `release-checklist.md`).

Para auditoría y handoff, es útil contar con un documento consolidado que resuma estado global y referencias clave.

## Decisión
Agregar un empaquetador de evidencia de sign-off:

1. **Script** `scripts/synology_signoff_package.py`
   - valida presencia de archivos base
   - valida estructura mínima del JSON de gate
   - genera `synology-signoff-package.md` consolidado

2. **Target Make** `synology-signoff-package`
   - ejecuta empaquetado con rutas configurables (`REPORT_PATH`, `JSON_PATH`, `CHECKLIST_PATH`, `PACKAGE_PATH`)

3. **Tests**
   - validación de generación exitosa
   - validación de falla por archivos faltantes

## Consecuencias
### Positivas
- Evidencia final centralizada para auditoría/handoff.
- Menor tiempo de revisión manual del estado operativo.

### Trade-offs
- Introduce un archivo más en cadena de artefactos.
- Debe mantenerse sincronizado con estructura de JSON/checklist.

## Guardrail
- No habilita live trading.
- Mantiene requisito de `PAPER_TRADING=true` en operación controlada.
