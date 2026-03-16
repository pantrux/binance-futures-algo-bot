# Roadmap de diseño e implementación

> Este documento se actualiza después de **cada PR**.
> Regla: ningún PR se considera cerrado sin actualizar roadmap + PR roadmap + docs/ADR + sync en Outline.

## Resumen ejecutivo

- **Estado global actual:** `PR-94` ya quedó mergeado en `main`, dejando la baseline UX de la trading workstation operativa con shell modular, drill-down por tabs, live polling y un order blotter interactivo.
- **PR activo:** `PR-95` — acotar el scroll/sticky del order blotter al contexto correcto y sincronizar el roadmap post-merge.
- **Siguiente carril sugerido:** cerrar este follow-up corto de hardening visual y luego pasar a la siguiente expansión funcional de la workstation (realtime más fino, acciones operativas o mayor densidad contextual por operación).

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
| Fase 13 — Profundización del command center | ✅ Completada | 100% | PR-53..PR-62 | historial operativo completo por `trade_plan_id`, smoke Synology específico, evidencia operacional del gate, corrección de precios reales, bloqueo de setups demo, auto-ingesta de mercado y normalización/hardening final de quantity hacia Binance |
| Fase 14 — Observabilidad operativa post-corrección | ✅ Completada | 100% | PR-63..PR-69 | metadata estructurada para errores/eventos y debugging más rápido sobre operación real en Synology, incluyendo consumo visual en el command center, resumen contextual del último riesgo, smoke automatizado de estos marcadores, cobertura testeable de sus ramas condicionales, mejor DX de fallos del helper CLI y cobertura local del contrato shell end-to-end |
| Fase 15 — Hardening del harness operacional | ✅ Completada | 100% | PR-70..PR-80 | teardown determinista, tipado explícito y cobertura reproducible de fallos de contrato/HTTP del shell smoke, incluyendo rutas base, auth opcional, dependencias externas configurables y marcadores críticos de la home web, para minimizar flakes y ambigüedad operativa en CI |


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

### PR-54 — Smoke Synology del command center enriquecido ✅
- smoke script endurecido para validar `GET /dashboard/command-center` y el payload enriquecido por operación
- smoke UI endurecido para exigir marcadores reales del dashboard (`Historial de órdenes`, `Historial de posiciones`, `Historial de riesgo`, `Reconcile actual`)
- validación real ejecutada con éxito contra NAS local (`192.168.0.8:8010` / `192.168.0.8:3012`)
- mergeado en `eefaa74`

### PR-55 — Deduplicar fetch web del smoke Synology ✅
- descargar la home del dashboard una sola vez por corrida
- validar múltiples marcadores UI sobre el mismo HTML para reducir tráfico y blips transitorios
- revalidación completa del smoke sobre el NAS real
- mergeado en `6f2bdb5`

### PR-56 — Evidencia operativa del command center para shadow run gate ✅
- enriquecer `synology_shadow_run_gate.py` con snapshot operacional del command center
- persistir bloque `command_center` dentro del artifact JSON del gate
- agregar sección Markdown con contexto de operaciones recientes + reconcile
- mergeado en `1850eec`

### PR-57 — Alinear docs del gate con evidencia del command center ✅
- runbook Synology exige revisar bloque `command_center` del artifact
- checklist de transición pide confirmación explícita de evidencia operacional reciente
- ADR-040 refleja que el gate ahora combina evidencia cuantitativa + operacional
- mergeado en `bbf0248`

### PR-58 — Persistir y backfillear precios reales desde Binance ✅
- usar `userTrades` como fuente de fill real por orden testnet
- persistir `order.price` y `position.entry_price` con fill real, no con precio planificado
- ejecutar backfill sobre órdenes/posiciones testnet ya abiertas en el NAS para corregir el command center actual
- mergeado en `db51dbb`

### PR-59 — Bloquear ejecución testnet desde señales demo ✅
- impedir que `meta.source != "market"` dispare órdenes reales en Binance Testnet
- permitir fallback a paper cuando `TESTNET_FALLBACK_TO_PAPER=true`
- validar con tests + despliegue del worker en Synology
- mergeado en `ea19847`

### PR-60 — Auto-ingestar mercado antes de caer a demo ✅
- si `/signals` o `/market/snapshot` no tienen insumos suficientes, el worker intenta `POST /market/ingest/{symbol}`
- tras la ingesta, reintenta el setup market-driven antes de declarar `snapshot_incompleto`
- validado en Synology: nuevas corridas del worker muestran `source="market"`, `reason="ok"` para BTC/ETH/SOL
- mergeado en `3d2b5a1`

### PR-61 — Normalizar cantidad testnet para Binance ✅
- serializar `quantity` sin artefactos float (`0.81`, `18.03`, no `0.8100000000000001` / `18.0300000000000011`)
- cubrir con tests la serialización limpia de cantidades
- validar en Synology que ETH/SOL dejen de fallar con `400 Bad Request`
- mergeado en `535c108`

### PR-62 — Hardening fino del serializer de quantity ✅
- rechazar `NaN` / infinitos en `_serialize_quantity()`
- usar `pytest.raises` para las validaciones de error
- cerrar observaciones menores post-merge del cliente Binance
- mergeado en `526f240`

### PR-63 — Metadata estructurada para `risk_events` ✅
- agregar columna JSON estructurada para contexto operativo de eventos críticos
- persistir `context` del motor de riesgo sin degradarlo a texto libre
- persistir detalles útiles de ejecución/reconcile en errores reales
- exponer esa metadata en command center para debugging más rápido
- mergeado en `00ad36b` y validado en Synology con eventos reales para BTC/ETH/SOL

### PR-64 — Hacer visible `risk_events.context_json` en la UI ✅
- tipar `context` en el frontend del command center
- renderizar chips/labels con metadata útil en historial de riesgo y feed global
- validar con `next build` y deploy posterior en Synology
- mergeado en `f14db14` y validado en Synology con `context-list`/`context-chip` visibles y `external_order_id` sin separadores de miles

### PR-65 — Resumen contextual del último riesgo por operación ✅
- agregar `latest_risk_context` al payload de `operation_snapshots`
- renderizar chips/contexto también en la celda resumen de riesgo del radar principal
- mantener consistencia visual entre resumen y drill-down
- mergeado en `9b1bb33` y validado en Synology con contexto visible en la celda resumen del radar principal

### PR-66 — Smoke Synology para contexto de riesgo ✅
- endurecer `scripts/synology_smoke_test.sh` para exigir `latest_risk_context` en API
- validar `context` en `recent_risk_events`
- exigir marcadores `context-list` / `context-chip` en la home del dashboard
- alinear runbook con el nuevo criterio mínimo de aprobación
- mergeado en `95e1c39` y validado en Synology con gating condicional para payload con/sin contexto

### PR-67 — Cobertura testeable del smoke para contexto ✅
- extraer la validación JSON del smoke a `scripts/synology_smoke_context_check.py`
- cubrir con tests reproducibles el caso de payload limpio/vacío
- cubrir con tests reproducibles el caso de payload con contexto útil
- mantener `scripts/synology_smoke_test.sh` como orquestador del smoke real sobre NAS
- mergeado en `bca67a6` y validado en Synology incluso ejecutando el smoke desde fuera de la raíz del repo

### PR-68 — Manejo limpio de errores CLI en el helper del smoke ✅
- agregar manejo explícito de `FileNotFoundError`, `JSONDecodeError` y `ValueError` en `main()`
- emitir mensajes claros a `stderr` sin tracebacks ruidosos
- cubrir los caminos de error del entrypoint con tests reproducibles
- mantener el contrato del shell smoke (`exit != 0` cuando el helper falla)
- mergeado en `c5396d7` y validado en Synology con `Greptile 5/5`

### PR-69 — Fixtures locales para el shell smoke ✅
- cubrir `scripts/synology_smoke_test.sh` end-to-end con un servidor fixture local
- probar payload con contexto + markers HTML presentes
- probar payload limpio sin markers HTML
- probar fallo cuando hay contexto pero faltan `context-list` / `context-chip`
- mergeado en `11eb418` y validado con `Greptile 4/5`, checks verdes y fixture shell robustecido

### PR-70 — Cierre formal de Fase 14 + hardening final del fixture shell ✅
- tipar explícitamente `run_fixture_server`
- centralizar el apagado del servidor fixture en un helper compartido
- verificar que el thread realmente termina tras `shutdown()` + `join()`
- cerrar formalmente Fase 14 y abrir Fase 15 en la documentación viva del repo
- mergeado en `6f5a580` con `Greptile 5/5`

### PR-71 — Cobertura shell para payload inválido del command center ✅
- agregar caso end-to-end donde `/dashboard/command-center` devuelve payload inválido
- validar que `synology_smoke_test.sh` falle propagando el error del helper de contexto
- dejar documentado el avance de Fase 15 sobre failure modes del harness
- mergeado en `5204364` con checks verdes y thread resuelto

### PR-72 — Cobertura shell para fallos HTTP base ✅
- extender el fixture HTTP local con overrides por ruta
- agregar caso end-to-end para `/health` no-200
- agregar caso end-to-end para `/metrics` inesperado sin auth
- validar que el shell smoke emita fallos claros en `stderr` para esos caminos
- mergeado en `43c1c1c` con `Greptile 5/5` y checks verdes

### PR-73 — Cobertura shell para summary y trade-plans ✅
- agregar caso end-to-end para `/dashboard/summary` no-200
- agregar caso end-to-end para `/trade-plans` no-200
- seguir cerrando failure modes HTTP base del shell smoke
- mergeado en `23400e5` con `Greptile 5/5` y checks verdes

### PR-74 — `/metrics` autenticado + cleanup de helpers del fixture ✅
- cubrir con fixture local el camino de `/metrics` cuando se usa `METRICS_API_KEY`
- validar éxito/fallo explícito del header `x-metrics-key`
- reducir duplicación menor en helpers del fixture shell donde aporte claridad sin tocar lógica productiva
- mergeado en `ba68d86` con checks verdes y reviews resueltos

### PR-75 — Cobertura shell para strictness de `testnet/ping` ✅
- cubrir el branch `STRICT_EXTERNAL_CHECKS=false` cuando `/integrations/binance/testnet/ping` falla
- cubrir el branch `STRICT_EXTERNAL_CHECKS=true` para asegurar fallo explícito
- mantener el harness reproducible sin depender de Binance real
- mergeado en `6e4bbd7` con checks verdes y review resuelta

### PR-76 — Failure modes de `WEB /` en el shell smoke ✅
- cubrir el caso donde la home web responde `non-200`
- cubrir el caso donde la home web responde `200` pero con body vacío
- mantener el harness reproducible y el diagnóstico claro para fallos de `fetch_body()`/marcadores web
- mergeado en `72dba40` con checks verdes y `Greptile 5/5`

### PR-77 — Marcadores faltantes de `WEB /` en el shell smoke ✅
- cubrir el caso donde la home responde `200` pero falta el marcador base `bot`
- cubrir el caso donde la home responde `200` pero falta un marcador central del command center
- mantener el harness reproducible y el diagnóstico claro para fallos de `check_body_contains()`
- mergeado en `533d884` con checks verdes y reviews resueltas

### PR-78 — Marcadores adicionales de `WEB /` en el shell smoke ✅
- cubrir el caso donde la home responde `200` pero falta `Detalle por trade plan`
- cubrir el caso donde la home responde `200` pero falta `Reconcile actual`
- mantener el harness reproducible y el diagnóstico claro para fallos adicionales de `check_body_contains()`
- mergeado en `26eaacc` con checks verdes y reviews resueltas

### PR-79 — Marcadores restantes de órdenes y posiciones en el shell smoke ✅
- cubrir el caso donde la home responde `200` pero falta `Historial de órdenes`
- cubrir el caso donde la home responde `200` pero falta `Historial de posiciones`
- cerrar la cobertura explícita pendiente de `check_body_contains()` sobre los marcadores base del command center
- mergeado en `6968007` con checks verdes y reviews resueltas

### PR-80 — Cierre formal de Fase 15 ✅
- consolidar documentalmente que el harness operacional quedó endurecido y reproducible
- dejar evidencia de cierre de fase en un documento dedicado
- preparar el roadmap para volver a lógica de producto/trading


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
