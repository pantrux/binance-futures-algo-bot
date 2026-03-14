# Roadmap de diseño e implementación

> Este documento se actualiza después de **cada PR**.
> Regla: ningún PR se considera cerrado sin actualizar roadmap + PR roadmap + docs/ADR + sync en Outline.

## Resumen ejecutivo

- **Estado global actual:** Fase 10 ya tiene contrato de drills/evidencia mergeado y ahora avanza hacia artefactos operativos reutilizables para cutover.
- **PR activo:** `PR-37` — templates operativos de artefactos de cutover.
- **Etapa actual:** **Fase 10 — Ensayos operativos de cutover** (`PR-36` a `PR-37`).

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
| Fase 3 — Planeación y riesgo avanzado | ⏳ Planificada | 0% | PR-25..PR-28 | Scoring/régimen/sizing/correlación/circuit breakers avanzados |
| Fase 4 — Ejecución | ✅ Completada (baseline) | 100% | PR-7, PR-9 | Ejecución paper market-driven + despliegue base |
| Fase 5 — Operación controlada | ✅ Completada | 100% | PR-8..PR-18 | Cadena operativa auditable completa |
| Fase 6 — Infraestructura recurrente | 🟡 En progreso | 85% | PR-22..PR-24 | Operación continua endurecida (SRE + continuidad) |
| Fase 7 — Riesgo cuantitativo operativo | 🔵 Planificada | 0% | PR-25..PR-28 | Motor de decisión de riesgo listo para testnet serio |
| Fase 8 — Ejecución exchange robusta | 🟡 En progreso | 75% | PR-29..PR-32 | Router testnet + reconciliación + paridad paper/testnet + reporting operativo |
| Fase 9 — Go-live readiness | ✅ Completada | 100% | PR-33..PR-35 | Validación cuantitativa, gates formales de transición y cutover controlado |
| Fase 10 — Ensayos operativos de cutover | 🟡 En progreso | 20% | PR-36 | drills sintéticos, evidencia estandarizada y cierre operacional pre-live |

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

## Fase 6 — Infraestructura recurrente y continuidad (en progreso)
**Inicio real:** `PR-20` mergeado (`fd5229d`), `PR-21` mergeado (`bd40a5f`), `PR-22` mergeado (`e303e83`), `PR-23` mergeado (`aa3a67f`) y continuación activa en `PR-24`.

### PR-20 — Estabilización del worker Synology (one-shot) ✅
- `worker.restart: "no"` para evitar restart loop
- operación base definida: servicios persistentes (`api/web/postgres/redis`) + jobs one-shot (`migrate/worker`)
- verificación operativa en NAS con healthchecks en verde

### PR-21 — Corrección documental post-merge ✅
- alineación de roadmap/master-plan/runbook con estado real post `PR-19`/`PR-20`
- sync de Outline validado (`docs_synced=42`)

### PR-22 — Retención y gobierno de artifacts ✅
- política 30/60/90 días
- limpieza automática de artifacts antiguos
- índice/reporte JSON por corrida (`synology-artifact-retention.json`)

### PR-23 — Observabilidad/alerting de infraestructura ✅
- alertas por fallos de gate, degradación de health y drift operativo
- tablero SLO operativo (disponibilidad de pipeline)
- workflow horario de observabilidad (`synology-observability-alerting.yml`) + reportes JSON/Markdown

### PR-24 — Resiliencia, recuperación y hardening operacional 🟡
- respaldo/restauración de configuración crítica
- playbook de disaster recovery probado con evidencia
- revisión de secretos/tokens/rotación + permisos/superficie de exposición

## Fase 7 — Planeación y riesgo avanzado

### PR-25 — Clasificador de régimen de mercado
### PR-26 — Sizing dinámico por volatilidad/riesgo
### PR-27 — Riesgo de portafolio y correlación multi-símbolo
### PR-28 — Gate de decisión final + circuit breakers avanzados

## Fase 8 — Ejecución exchange robusta

### PR-29 — Router Binance Testnet (orden real en entorno seguro)
### PR-30 — Reconciliación de órdenes/posiciones y máquina de estados
### PR-31 — Paridad paper vs testnet + shadow run
### PR-32 — Alerting y reporting de producción

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

## Fase 10 — Ensayos operativos de cutover

### PR-36 — Drills sintéticos y paquete de evidencia de cutover ✅
- ver `docs/plans/cutover-drills-and-evidence-package.md`
- ADR-037

### PR-37 — Templates operativos de artefactos de cutover 🟡
- ver `docs/templates/README.md`
- ADR-038

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
