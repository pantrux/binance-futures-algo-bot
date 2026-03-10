# Roadmap de diseño e implementación

> Este documento debe mantenerse actualizado después de **cada PR**.
> Regla del proyecto: cada PR debe reflejar su avance en este roadmap y en la documentación asociada.

## Resumen ejecutivo

- **Estado global actual:** Fase 2 en ejecución
- **Último hito consolidado:** capa base de señales y feature engineering inicial mergeada (`PR-6`)
- **Trabajo activo:** preparación de `PR-7` — worker market-driven

## Gantt textual de avance

| Fase | Estado | Avance estimado | Observaciones |
|---|---|---:|---|
| Fase 0 — Fundación | ✅ Completada | 100% | Monorepo, ADRs, CI, dashboard base, RiskEngine, baseline Synology-first |
| Fase 1 — Integración de mercado | ✅ Completada | 100% | Ingesta OHLCV/snapshots, hardening de mercado, base persistida para análisis |
| Fase 2 — Señales | 🟡 En progreso | 60% | Indicadores técnicos base y señales derivadas iniciales listos; faltan patrones, sentimiento y señales más avanzadas |
| Fase 3 — Planeación y riesgo | ⏳ Pendiente | 0% | Régimen, sizing dinámico, circuit breakers, correlación |
| Fase 4 — Ejecución | ⏳ Pendiente | 0% | Binance Futures Testnet, órdenes, fills, sincronización de estado |
| Fase 5 — Operación controlada | ⏳ Pendiente | 0% | Alertas, reportes, despliegue progresivo, operación controlada |

---

## Fase 0 — Fundación
**Estado:** ✅ Completada

### Entregado
- Monorepo
- ADRs y diagramas base
- CI inicial
- dashboard base
- motor de riesgo inicial
- baseline Synology-first (Dockerfiles + compose objetivo)
- workflow formal por PR
- paper trading y dominio operativo base

### PRs / hitos relacionados
- bootstrap inicial en `main`
- `PR-1` — workflow por PR

---

## Fase 1 — Integración de mercado
**Estado:** ✅ Completada

### Entregado
- OHLCV persistido
- snapshots de mercado
- funding / open interest base
- hardening de ingesta Binance
- deduplicación/idempotencia de candles
- base sólida para cálculo técnico

### PRs / hitos relacionados
- `PR-2` — ingesta inicial de mercado Binance
- `PR-3` — hardening de ingesta de mercado
- `PR-4` — hardening post-merge de ingesta

### Pendiente de esta fase
- websockets en tiempo real (se puede tratar como subfase futura si aporta a ejecución)
- snapshots de liquidez más profundos si la estrategia los requiere

---

## Fase 2 — Señales
**Estado:** 🟡 En progreso

### Entregado
- indicadores técnicos base:
  - EMA
  - RSI
  - ATR
  - momentum
- endpoint de snapshot técnico
- metadata de frescura (`last_candle_close_ms`)

### En progreso
- señales derivadas / feature engineering inicial:
  - `trend_bias`
  - `momentum_bias`
  - `volatility_regime`
  - `ema_spread_pct`
  - `atr_pct`

### Pendiente
- patrones de velas
- sentimiento
- señales/fundamental crypto-native
- consolidación de features para consumo del worker

### PRs / hitos relacionados
- `PR-5` — indicadores técnicos base ✅
- `PR-6` — señales y features técnicos base ✅

---

## Fase 3 — Planeación y riesgo
**Estado:** ⏳ Pendiente

### Alcance esperado
- clasificador de régimen
- sizing dinámico
- circuit breakers
- correlación entre exposiciones
- scoring/gating previo al trade plan

### Dependencia
Requiere cerrar la capa de señales base de la Fase 2.

---

## Fase 4 — Ejecución
**Estado:** ⏳ Pendiente

### Alcance esperado
- Binance Futures Testnet
- órdenes y fills
- sincronización de estado
- worker market-driven operativo

### Dependencia
Requiere planeación/riesgo suficientemente estable.

---

## Fase 5 — Operación controlada
**Estado:** ⏳ Pendiente

### Alcance esperado
- alertas
- reportes
- despliegue progresivo
- operación controlada
- guardrails finales antes de cualquier trading real

---

## Regla operativa permanente

Después de **cada PR** se debe actualizar como mínimo:
1. este roadmap (`docs/plans/implementation-roadmap.md`)
2. el roadmap de PRs (`docs/pr-plan/PR_ROADMAP.md`)
3. la documentación técnica/ADR afectada
4. Outline, si el endpoint está disponible
5. memoria operativa del proyecto
