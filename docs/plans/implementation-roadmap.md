# Roadmap de diseño e implementación

> Este documento se actualiza después de **cada PR**.
> Regla: ningún PR se considera cerrado sin actualizar roadmap + PR roadmap + docs/ADR + sync en Outline.

## Resumen ejecutivo

- **Estado global actual:** `PR-53` ya quedó mergeado en `main` y el command center enriquecido fue desplegado/validado en Synology; el foco inmediato pasa a convertir esa validación real en smoke auditable y reutilizable.
- **PR activo:** `PR-54` — smoke Synology del command center enriquecido.
- **Siguiente carril sugerido:** cerrar `PR-54` y luego evaluar evidencia operativa del shadow run con la nueva vista ya desplegada en NAS.

## ¿Cuándo comienza a levantarse la infraestructura del bot?

La infraestructura base **ya comenzó y quedó levantada** en:
- `PR-9` (despliegue real en Synology + smoke)
- `PR-10` (preflight)
- `PR-11` (release gate unificado)

El levantamiento de infraestructura recurrente ya arrancó con `PR-20` (estabilización worker one-shot), `PR-21` (corrección documental), `PR-22` (retención de evidencia) y continúa en `PR-23` con observabilidad/alerting operacional.

---

## Gantt textual de avance (plan cerrado)

| Fase | Estado | Avance | PRs | Resultado esperado |
|---|---|---:|---|---|
| Fase 0 — Fundación | ✅ Completada | 100% | PR-1 | Gobierno de repo, workflow por PR, base técnica y documental |
| Fase 1 — Integración de mercado | ✅ Completada | 100% | PR-2, PR-3, PR-4 | Ingesta OHLCV/snapshots robusta e idempotente |
| Fase 2 — Señales | ✅ Completada | 100% | PR-5, PR-6, PR-7 | Indicadores + señales + worker market-driven |
| Fase 3 — Planeación y riesgo avanzado | ✅ Completada | 100% | PR-25..PR-28 | scoring/régimen/sizing/correlación/circuit breakers avanzados operativos |
| Fase 4 — Ejecución | ✅ Completada (baseline) | 100% | PR-7, PR-9 | ejecución paper market-driven + despliegue base |
| Fase 5 — Operación controlada | ✅ Completada | 100% | PR-8..PR-18 | cadena operativa auditable completa |
| Fase 6 — Infraestructura recurrente | ✅ Completada | 100% | PR-22..PR-24 | operación continua endurecida (SRE + continuidad) |
| Fase 7 — Riesgo cuantitativo operativo | ✅ Completada | 100% | PR-25..PR-28 | motor de decisión de riesgo listo para testnet serio |
| Fase 8 — Ejecución exchange robusta | ✅ Completada | 100% | PR-29..PR-32 | router testnet + reconciliación + paridad paper/testnet + reporting operativo |
| Fase 9 — Go-live readiness | ✅ Completada | 100% | PR-33..PR-35 | validación cuantitativa, gates formales de transición y cutover controlado |
| Fase 10 — Ensayos operativos de cutover | ✅ Completada | 100% | PR-36..PR-39 | drills sintéticos, evidencia estandarizada, templates operativos y navegación documental usable en Outline |
| Fase 11 — Guardrails documentales + readiness automation | ✅ Completada | 100% | PR-40..PR-41 | lint documental + gate auditable de shadow run desplegado en Synology |
| Fase 12 — Activación operativa de testnet | ✅ Completada | 100% | PR-42..PR-52 | primeras ejecuciones testnet reales + command center enriquecido + persistencia del fill real + hardening fino del refresh testnet |
| Fase 13 — Profundización del command center | 🟡 En progreso | 45% | PR-53..PR-55 | historial operativo completo por `trade_plan_id`, smoke Synology específico y trazabilidad end-to-end validada en NAS |

---

## Plan detallado por etapa (de principio a fin)

## Fase 0 — Fundación (cerrada)
**PRs:** PR-1  
**Entregado:** estructura de repo, reglas de PR, base ADR/docs, baseline CI.

## Fase 1 — Integración de mercado (cerrada)
**PRs:** PR-2, PR-3, PR-4  
**Entregado:** ingesta Binance endurecida, deduplicación, estabilidad de datos.

## Fase 2 — Señales (cerrada)
**PRs:** PR-5, PR-6, PR-7  
**Entregado:** indicadores, señales derivadas, worker híbrido market-driven con fallback controlado.

## Fase 4/5 — Ejecución + operación controlada (cerrada)
**PRs:** PR-8 a PR-18  
**Entregado:** observabilidad, smoke, preflight, release gate, JSON summary, verify, checklist, sign-off package y cierre formal de fase.

## Fase 6 — Infraestructura recurrente y continuidad (completada)
**Estado real:** completada con `PR-22`, `PR-23` y `PR-24` mergeados.

### Entregables consolidados
- retención y gobierno de artifacts operacionales
- observabilidad/alerting de infraestructura
- resiliencia, backup/restore y hardening operacional base
- documentación y runbooks alineados con operación real en Synology

## Fase 7 — Riesgo cuantitativo operativo (completada)

### Entregables consolidados (`PR-25`..`PR-28`)
- clasificador de régimen de mercado
- sizing dinámico por volatilidad/riesgo
- guardrails de portafolio y correlación multi-símbolo
- gate final de decisión con circuit breakers avanzados

## Fase 8 — Ejecución exchange robusta (completada)

### Entregables consolidados (`PR-29`..`PR-32`)
- router Binance Testnet para ejecución segura
- reconciliación de órdenes/posiciones y máquina de estados
- shadow run paper vs testnet
- alerting y reporting de producción

## Fase 9 — Go-live readiness

### PR-33 — Backtesting/walk-forward y benchmark de estrategia ✅
- servicio `BacktestingService` con estrategia baseline `ema_rsi_baseline`
- benchmark `buy_and_hold` del mismo activo y periodo
- endpoint `POST /backtesting/run`
- métricas reproducibles: retorno, win rate, profit factor, drawdown y trades
- walk-forward simple con ventanas in-sample / out-of-sample y selección explícita de parámetros
- ADR-034
### PR-34 — Checklist formal de transición y política de rampa de capital ✅
- ver `docs/plans/transition-checklist-and-capital-ramp.md`
- ADR-035
### PR-35 — Cutover controlado (si y solo si todos los gates pasan) ✅
- ver `docs/plans/cutover-and-post-cutover-monitoring.md`
- ADR-036

## Fase 10 — Ensayos operativos de cutover ✅

### PR-36 — Drills sintéticos y paquete de evidencia de cutover ✅
- ver `docs/plans/cutover-drills-and-evidence-package.md`
- ADR-037

### PR-37 — Templates operativos de artefactos de cutover ✅
- ver `docs/templates/README.md`
- ADR-038

### PR-39 — Links navegables para documentación sincronizada en Outline ✅
- estrategia híbrida: URL de Outline si el documento existe allí; fallback a GitHub `blob/<ref>`
- script `scripts/sync_outline_docs.py`
- ADR-039
- continuidad retomada desde el PR-38 cerrado por renombre de rama
- sync post-merge validado (`docs_synced=59`, `duplicates_archived=0`, `unknown_archived=0`)

## Fase 11 — Guardrails documentales + readiness automation

### PR-40 — Validación CI de links Markdown documentales ✅
- script `scripts/check_markdown_links.py`
- validación de links locales antes del sync a Outline
- job dedicado en CI para lint + tests focales
- mergeado en `d517c3c`

### PR-41 — Gate auditable de shadow run para readiness testnet ✅
- `ShadowRunReportingService` + endpoint `GET /reporting/shadow-run-summary`
- workflow `synology-shadow-run-gate.yml`
- script `scripts/synology_shadow_run_gate.py`
- ADR-040
- mergeado en `d486e63`
- desplegado en Synology y validado con primer gate real (`paper=63`, `testnet=0`, `duration_days=3.0494`, `overall=FAIL`)

## Fase 12 — Activación operativa de testnet (completada)

### Estado consolidado reciente
- **PR-42** ✅ — activación real de shadow run testnet en Synology.
- **PR-43** ✅ — normalización de fills testnet y reconciliación base.
- **PR-44** ✅ — guard para rechazos históricos en reconciliación.
- **PR-45** ✅ — centro de mando operacional inicial.
- **PR-46** ✅ — radar unificado por operación.
- **PR-47** ✅ — línea de tiempo operativa unificada.
- **PR-48** ✅ — drill-down por trade plan.
- **PR-49** ⚪ — cerrado sin merge; branch fallido/superado y absorbido por la secuencia posterior.
- **PR-50** ✅ — justificación técnica por orden visible en el command center.
- **PR-51** ✅ — persistencia de fill real desde Binance Testnet mediante refresh post-submit y derivación defensiva del precio/cantidad ejecutados.
- **PR-52** ✅ — hardening residual del refresh testnet: evita refresh innecesario en `PARTIALLY_FILLED` completos y blinda fallback por `clientOrderId`.

## Fase 13 — Profundización del command center (en progreso)

### PR-53 — Historial operativo completo por `trade_plan_id` ✅
- payload enriquecido por operación para órdenes, posiciones, risk events y timeline asociada
- vista detallada para inspección end-to-end sin joins manuales
- mergeado en `f5368c8`

### PR-54 — Smoke Synology del command center enriquecido 🟡
- smoke script endurecido para validar `GET /dashboard/command-center` y el payload enriquecido por operación
- smoke UI endurecido para exigir marcadores reales del dashboard (`Historial de órdenes`, `Historial de posiciones`, `Historial de riesgo`, `Reconcile actual`)
- validación real ya ejecutada con éxito contra NAS local (`192.168.0.8:8010` / `192.168.0.8:3012`)

---

## Resultado final esperado

Un sistema de trading **auditable, operable y seguro**, con:
1. pipeline completo de datos→señales→riesgo→ejecución,
2. operación recurrente endurecida en Synology,
3. evidencia automática de cada release/gate,
4. criterio formal y medible para eventual transición fuera de paper,
5. documentación sincronizada y ordenada de extremo a extremo (repo + Outline).

## Guardrails permanentes

- `PAPER_TRADING=true` obligatorio hasta cumplir criterios de transición definidos en Fase 9 y aprobar los ensayos operativos de Fase 10.
- No habilitar live trading por defecto en ninguna fase intermedia.
- Cada PR debe cerrar con: checks verdes + comentarios/reviews resueltos + roadmap/docs/memoria actualizados.
