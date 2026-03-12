# ADR-028 — Guardrails de riesgo de portafolio y correlación multi-símbolo

## Estado
Aceptado

## Contexto
Con `ADR-027` el sizing ya era dinámico por score/régimen/volatilidad para una operación individual. Faltaba cubrir un riesgo estructural: **sobreexposición agregada** cuando existen posiciones abiertas correlacionadas.

Casos típicos del problema:
- abrir un nuevo long en `BTCUSDT` cuando ya hay exposición relevante en clúster BTC/ETH,
- mantener riesgo total de cuenta dentro de 5% pero concentrado en un mismo clúster,
- aceptar `regime_confidence` externo sin trazabilidad de impacto en riesgo agregado.

## Decisión
Agregar una capa de riesgo de portafolio en `RiskEngine` con:

1. **Estado de portafolio opcional en request**
   - `portfolio_state.positions[]` con `symbol`, `side`, `notional_usdt`, `risk_pct`
   - límites configurables por request:
     - `max_portfolio_risk_pct`
     - `max_cluster_risk_pct`
     - `max_symbol_risk_pct`
   - `correlation_guard_enabled`

2. **Clustering operativo de símbolos**
   - `BTC_CORE`, `ETH_CORE`, `LARGE_ALT`, `ALTS`
   - clasificación simple y determinística por ticker

3. **Matriz operativa de correlación**
   - coeficientes por par de clústeres para estimar presión de correlación
   - multiplicador de degradación (`correlation_multiplier`) cuando la presión es alta

4. **Gates agregados antes de aprobar sizing final**
   - límite global de portafolio
   - límite por símbolo
   - límite por clúster correlacionado
   - posibilidad de recortar (`cap`) o bloquear la operación según headroom

5. **Eventos de riesgo enriquecidos**
   - `RiskDecision` expone métricas antes/después (portfolio/symbol/cluster)
   - `risk_events[]` con tipo, severidad y contexto
   - `TradePlanService` persiste estos eventos en tabla `risk_events` con mensaje plano enriquecido (`key=value`) para facilitar búsquedas operativas sin parseo JSON

## Consecuencias
- Menor probabilidad de concentración de riesgo por activos correlacionados.
- Mejor trazabilidad de por qué una operación fue aprobada, recortada o bloqueada.
- Compatibilidad hacia atrás: si no llega `portfolio_state`, el motor opera con defaults conservadores.

## Guardrails
- Se conserva el límite global de cuenta (`max_account_risk_pct=5%`) como techo duro.
- El gate de correlación no puede relajar guardrails previos: solo mantener o reducir sizing.
- Si un límite agregado queda sin headroom, la operación se bloquea explícitamente con razón auditable.
