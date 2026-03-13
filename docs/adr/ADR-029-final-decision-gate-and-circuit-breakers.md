# ADR-029 — Gate final de decisión y circuit breakers

## Estado
Aceptado

## Contexto
Con PR-27 se reforzó riesgo de portafolio/correlación, pero faltaba una capa final explícita de autorización/rechazo que consolidara condiciones de mercado y protección operativa antes de aprobar definitivamente un trade plan.

## Decisión
Introducir `FinalDecisionGate` como capa posterior al `RiskEngine` con:

1. **Score compuesto final**
   - combina `score` del motor de riesgo, `regime_confidence` y `liquidity_score`.
   - para evitar doble conteo de liquidez, el componente base descuenta la contribución de liquidez ya embebida en `RiskEngine.aggregate_score` antes de aplicar ponderación.

2. **Circuit breakers explícitos**
   - volatilidad extrema,
   - liquidez crítica,
   - sobrecalentamiento de portafolio,
   - riesgo de portafolio desconocido (fail-safe),
   - incertidumbre de régimen.

3. **Contrato de salida enriquecido**
   - `RiskDecision` agrega:
     - `final_gate_score`
     - `final_gate_passed`
     - `final_gate_reason`
     - `triggered_breakers`

4. **Persistencia auditable**
   - eventos del gate final se anexan a `risk_events` y se persisten junto al trade plan.

## Consecuencias
- Mayor control antes de ejecutar el trade plan.
- Trazabilidad de bloqueos por breaker en DB y documentación.
- Compatibilidad hacia atrás: si no se activan breakers y el score final es suficiente, el flujo permanece aprobado.

## Guardrails
- El gate final nunca aumenta exposición; solo mantiene o bloquea.
- Si un breaker se dispara, el trade queda bloqueado y `suggested_risk_pct/max_position_notional` pasan a cero.
