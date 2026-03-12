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
   - umbrales **relativos** a `min_score_to_trade` (default `60`)
   - `score >= min+25 -> 1.15`
   - `score >= min+15 -> 1.00`
   - `score >= min+5 -> 0.80`
   - `score >= min -> 0.65`
   - `score < min -> 0` (no trade)

   Con la configuración default (`min=60`) esto equivale a los buckets absolutos `85/75/65/60`.

2. **regime_multiplier** (contexto de mercado):
   - `alta_volatilidad`: degradación escalonada según `regime_confidence`
   - `transicion`: degradación moderada
   - `rango_lateral`: degradación conservadora
   - `tendencia_alcista|tendencia_bajista`: neutro/bonus leve si confianza alta
   - `unknown`: bloqueo (`0`)

   Guardrail adicional: si `volatility_pct >= 4.0`, el multiplicador de régimen efectivo
   queda capped al máximo permitido por `alta_volatilidad`, calculado con confianza
   derivada de la volatilidad observada (`volatility_pct`), incluso cuando llega un
   `market_regime` explícito optimista (protección contra régimen externo obsoleto).

3. **volatility_multiplier** (presión de volatilidad observada):
   - degradación progresiva por bandas de `volatility_pct`
   - las bandas se anclan al `high_volatility_threshold_pct` configurable de política

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
- Mejor trazabilidad para PR-27 (riesgo de portafolio/correlación), ya que la salida de riesgo expone `market_regime` y `regime_confidence` junto al sizing aplicado.
- Se mantiene compatibilidad hacia atrás: callers que no envían régimen siguen operando con fallback.

## Guardrails
- No se modifica el límite global del 5% ni el tope de 1.25% por trade.
- Si no hay margen de riesgo disponible o `stop_distance<=0`, se mantiene bloqueo explícito.
- `high_volatility_threshold_pct` de política se valida con mínimo `>=2.0` para mantener el orden semántico de buckets de volatilidad.
