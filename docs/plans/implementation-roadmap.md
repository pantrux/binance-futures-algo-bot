# Roadmap de diseño e implementación

> Este documento debe mantenerse actualizado después de **cada PR**.
> Regla del proyecto: cada PR debe reflejar su avance en este roadmap y en la documentación asociada.

## Resumen ejecutivo

- **Estado global actual:** Fase 5 completada en modo de operación controlada (NAS)
- **Último hito consolidado:** workflow completo de sign-off mergeado (`PR-17`)
- **Trabajo activo:** `PR-18` — cierre formal de fase operativa

## Gantt textual de avance

| Fase | Estado | Avance estimado | Observaciones |
|---|---|---:|---|
| Fase 0 — Fundación | ✅ Completada | 100% | Monorepo, ADRs, CI, dashboard base, RiskEngine, baseline Synology-first |
| Fase 1 — Integración de mercado | ✅ Completada | 100% | Ingesta OHLCV/snapshots, hardening de mercado, base persistida para análisis |
| Fase 2 — Señales | ✅ Completada | 100% | Indicadores + señales derivadas + worker híbrido market-driven entregados |
| Fase 3 — Planeación y riesgo | 🟡 En progreso | 80% | Risk engine operativo, hardening continuo de score/gating pendiente fino |
| Fase 4 — Ejecución | ✅ Completada | 100% | Worker market-driven + despliegue Synology base + smoke operativo (PR-9) |
| Fase 5 — Operación controlada | ✅ Completada | 100% | Cadena operativa completa implementada (preflight/smoke/release/summary/verify/checklist/package); cierre documental formal completado en PR-18 |

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
**Estado:** ✅ Completada

### Entregado
- indicadores técnicos base:
  - EMA
  - RSI
  - ATR
  - momentum
- endpoint de snapshot técnico
- metadata de frescura (`last_candle_close_ms`)
- señales derivadas / feature engineering:
  - `trend_bias`
  - `momentum_bias`
  - `volatility_regime`
  - `ema_spread_pct`
  - `atr_pct`
- consumo operativo desde worker híbrido market-driven con fallback demo controlado

### Pendiente (mejora continua)
- patrones de velas avanzados
- sentimiento/fundamental crypto-native adicional
- features experimentales para modelos posteriores

### PRs / hitos relacionados
- `PR-5` — indicadores técnicos base ✅
- `PR-6` — señales y features técnicos base ✅
- `PR-7` — worker híbrido market-driven ✅

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
**Estado:** 🟡 En progreso

### Alcance entregado/parcial
- worker market-driven operativo
- flujo paper trading con órdenes/fills simulados
- sincronización de estado base para dashboard

### Alcance pendiente
- mejoras incrementales de resiliencia bajo carga y observabilidad avanzada

### Dependencia
Fase cerrada con PR-9; mejoras futuras pasan a Fase 5 (operación controlada).

---

## Fase 5 — Operación controlada
**Estado:** ✅ Completada

### Alcance entregado
- observabilidad baseline (métricas + logs estructurados)
- endpoint de métricas con auth opcional
- hardening de configuración/errores en worker y API

### Cierre formal (PR-18)
- documento formal de cierre de fase 5
- consolidación de criterios de aceptación cumplidos
- recomendaciones para continuidad de operación controlada

### Guardrails
- live trading sigue deshabilitado
- mantener `PAPER_TRADING=true` como condición vigente

---

## Regla operativa permanente

Después de **cada PR** se debe actualizar como mínimo:
1. este roadmap (`docs/plans/implementation-roadmap.md`)
2. el roadmap de PRs (`docs/pr-plan/PR_ROADMAP.md`)
3. la documentación técnica/ADR afectada
4. Outline, si el endpoint está disponible
5. memoria operativa del proyecto
