# ADR-027 — Sizing dinámico por volatilidad y régimen

## Estado
Aceptado

## Contexto
Con `ADR-026` ya existe `regime` + `regime_confidence` para describir contexto de mercado. Faltaba convertir ese contexto en una política cuantitativa de tamaño de posición dentro de `RiskEngine`, sin romper los guardrails existentes:

- riesgo agregado máximo de cuenta = 5%
- tope por trade = 1.25%
- bloqueo por score bajo

Además, en `alta_volatilidad` la confianza puede ser baja cerca del umbral de clasificación (`atr_pct≈2.5%`), por lo que el degradado de sizing debe ser explícito y no binario.

## Decisión
Introducir un modelo de sizing dinámico multiplicativo en `RiskEngine`:

`risk_pct = base_risk_per_trade * score_multiplier * regime_multiplier * volatility_multiplier`

con clamp final a `max_single_trade_pct`.

### Factores
1. **score_multiplier** (calidad del setup):
   - `>=85 -> 1.15`
   - `>=75 -> 1.00`
   - `>=65 -> 0.80`
   - `>=60 -> 0.65`
   - `<60 -> 0` (no trade)

2. **regime_multiplier** (contexto de mercado):
   - `alta_volatilidad`: degradación escalonada según `regime_confidence`
   - `transicion`: degradación moderada
   - `rango_lateral`: degradación conservadora
   - `tendencia_alcista|tendencia_bajista`: neutro/bonus leve si confianza alta
   - `unknown`: bloqueo (`0`)

3. **volatility_multiplier** (presión de volatilidad observada):
   - degradación progresiva por bandas de `volatility_pct`

### Integración de inputs
- `MarketState` incorpora campos opcionales:
  - `market_regime`
  - `regime_confidence`
- Si no llegan desde el caller, el motor aplica fallback:
  - clasifica régimen por `trend_strength` + `volatility_pct`
  - estima confianza de régimen de forma determinística

### Integración worker/API
- Worker consume `GET /market/regime/{symbol}` y propaga `market_regime/regime_confidence` en `market_state` al crear trade plans.

## Consecuencias
- Sizing más sensible al contexto real, no solo al score agregado.
- Menor exposición en volatilidad alta severa y en transición.
- Mejor trazabilidad para PR-27 (riesgo de portafolio/correlación), ya que el sizing por símbolo queda más contextualizado.
- Se mantiene compatibilidad hacia atrás: callers que no envían régimen siguen operando con fallback.

## Guardrails
- No se modifica el límite global del 5% ni el tope de 1.25% por trade.
- Si no hay margen de riesgo disponible o `stop_distance<=0`, se mantiene bloqueo explícito.
