# ADR-016 — Evidencia JSON para release gate Synology

## Estado
Aceptado (PR-12)

## Contexto
El release gate unificado (PR-11) ya genera reporte Markdown, útil para lectura humana pero limitado para automatización y auditoría machine-to-machine.

Se requiere una salida estructurada para:
- validaciones automáticas en CI/CD
- integraciones futuras (alertas, dashboards, históricos)
- inspección rápida de `PASS/FAIL` por etapa

## Decisión
Agregar una capa de resumen JSON al release gate:

1. **Parser dedicado**
   - `scripts/synology_release_gate_summary.py`
   - toma `synology-release-gate.md`
   - produce `synology-release-gate.json` con:
     - `overall`
     - `steps[]`
     - `step_count`

2. **Workflow actualizado**
   - `synology-release-gate.yml` ejecuta parser en `if: always()`
   - sube artifacts Markdown + JSON
   - publica JSON en `GITHUB_STEP_SUMMARY`

## Consecuencias
### Positivas
- Evidencia auditable por humanos y máquinas.
- Menor fricción para futuras automatizaciones operativas.
- Diagnóstico más rápido desde UI de Actions.

### Trade-offs
- Acoplamiento del parser al formato del Markdown actual.
- Si cambia el formato del reporte, hay que ajustar regex del parser.

## Guardrail
- Sigue prohibido habilitar live trading en este gate.
- `PAPER_TRADING=true` se mantiene como condición de operación controlada.
