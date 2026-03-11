# ADR-017 — Verificación estructural del JSON del release gate

## Estado
Aceptado (PR-13)

## Contexto
Con PR-12 se incorporó un resumen JSON del release gate. Aun así, faltaba una validación explícita de estructura/consistencia para evitar que un JSON malformado o incompleto pase desapercibido en CI.

## Decisión
Agregar verificación automática del JSON del gate:

1. **Script validador**
   - `scripts/synology_release_gate_verify.py`
   - valida campos requeridos:
     - `overall`
     - `steps`
     - `step_count`
   - valida consistencia:
     - `step_count == len(steps)`
     - estados de pasos en `{PASS, FAIL}`
     - nombres de pasos no vacíos
     - orden esperado configurable (default: `Preflight,Smoke`)

2. **Integración en workflow**
   - `synology-release-gate.yml` ejecuta validación del JSON en `if: always()`
   - falla el job si la evidencia JSON no cumple contrato estructural

3. **Tests unitarios**
   - cobertura de casos válidos e inválidos del verificador

## Consecuencias
### Positivas
- Mayor confianza en evidencia máquina-legible.
- Menor riesgo de consumir JSON corrupto en automatizaciones futuras.
- Criterio explícito de aceptación estructural en CI.

### Trade-offs
- Aumenta mantenibilidad por contrato más estricto.
- Cambios de formato del JSON requieren actualizar verificador/tests.

## Guardrail
- No cambia política de trading.
- `PAPER_TRADING=true` sigue obligatorio en gates operativos.
