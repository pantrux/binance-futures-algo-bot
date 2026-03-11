# ADR-021 — Workflow completo de sign-off operacional

## Estado
Aceptado (PR-17)

## Contexto
El stack ya dispone de scripts separados para gate, resumen JSON, verificación estructural, checklist y paquete final. Aún faltaba integrar todas esas piezas en una única corrida CI para minimizar pasos manuales y errores de orquestación.

## Decisión
Extender `synology-release-gate.yml` para ejecutar pipeline completo de sign-off:

1. release gate (preflight + smoke)
2. resumen JSON
3. verificación estructural JSON
4. generación checklist de aprobación
5. generación paquete consolidado de sign-off
6. upload de todos los artifacts

Además, exponer parámetros de sign-off en `workflow_dispatch`:
- `signoff_owner`
- `signoff_notes`

## Consecuencias
### Positivas
- Menos fricción operacional.
- Mayor trazabilidad en una única corrida CI.
- Handoff más limpio con artifacts completos.

### Trade-offs
- Workflow más largo y con mayor superficie de mantenimiento.
- Dependencia explícita de formato/contrato entre scripts.

## Guardrail
- No habilita live trading.
- `PAPER_TRADING=true` se mantiene obligatorio.
