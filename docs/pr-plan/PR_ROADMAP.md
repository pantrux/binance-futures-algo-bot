# Plan formal de PRs — Binance Futures Algo Bot

## Regla operativa del proyecto
A partir de este punto, todo cambio funcional, de infraestructura o documentación relevante debe entrar por **Pull Request**.

## Reglas obligatorias
1. **1 rama = 1 PR = 1 objetivo claro**.
2. Todo PR debe incluir documentación actualizada en `docs/` y reflejo en Outline si hubo cambio de diseño o implementación.
3. Ningún PR se mergea sin checks en verde.
4. Si el merge lo realiza Skynet, debe revisar primero **todos** los comentarios/reviews humanos y de bots.
5. Si una sugerencia aplica, se incorpora antes del merge.
6. Si una sugerencia no aplica, se responde con justificación y se deja resuelta/cerrada según corresponda.
7. Título obligatorio: `PR-{NÚMERO}: {TÍTULO}`.
8. Configurar y mantener branch protection sobre `main` para exigir PRs y checks requeridos cuando el repositorio ya esté estabilizado operativamente.
9. **Regla de documentación permanente:** después de cada PR se debe actualizar el roadmap, el estado de avance y la documentación afectada.
10. **Regla Gantt permanente:** el proyecto debe mantener un Gantt/tabla de avance visible y actualizado para distinguir etapas completadas, en progreso y pendientes.
11. **Regla Greptile de oro:** leer siempre resumen + comentarios; resolver cada comentario antes de merge. Objetivo por defecto: `Confidence Score 5/5`, salvo instrucción explícita del owner.

## Estado actual del proyecto
Las fases fundacionales iniciales fueron empujadas directamente a `main` para bootstrap del repo greenfield. Desde este documento en adelante, el proyecto migra formalmente a workflow por PR.

## Estado consolidado de PRs

| PR | Título | Estado | Resultado |
|---|---|---|---|
| PR-1 | Gobierno del repositorio y workflow por PR | ✅ Mergeado | workflow formal por PR habilitado |
| PR-2 | Ingesta inicial de mercado Binance | ✅ Mergeado | OHLCV + snapshots persistidos |
| PR-3 | Hardening de ingesta de mercado | ✅ Mergeado | robustez de ingesta mejorada |
| PR-4 | Hardening post-merge de ingesta | ✅ Mergeado | idempotencia/concurrencia afinadas |
| PR-5 | Indicadores técnicos base | ✅ Mergeado | capa EMA/RSI/ATR/Momentum disponible |
| PR-6 | Señales y features técnicos base | ✅ Mergeado | señales derivadas iniciales listas para preparar el worker |
| PR-7 | Worker híbrido market-driven con fallback demo | ✅ Mergeado | worker market-driven operativo con fallback controlado |
| PR-8 | Observabilidad y hardening operativo | ✅ Mergeado | métricas, logs estructurados y controles de hardening operativo |
| PR-9 | Despliegue real en Synology con smoke tests | ✅ Mergeado | gate de smoke en Synology + workflow manual + ADR-013 |
| PR-10 | Preflight de configuración Synology | ✅ Mergeado | validación previa de `.env` + compose config + ADR-014 |
| PR-11 | Release gate unificado Synology | ✅ Mergeado | preflight + smoke + reporte auditable en una sola corrida |
| PR-12 | Resumen JSON y evidencia máquina-legible del gate | ✅ Mergeado | parser y artifacts JSON para auditoría automatizable |
| PR-13 | Verificación automática del JSON del gate | ✅ Mergeado | validador estructural + checks de consistencia de pasos |
| PR-14 | Atajos operativos con Makefile | ✅ Mergeado | ejecución estandarizada de preflight/smoke/release gate |
| PR-15 | Checklist de aprobación operacional | ✅ Mergeado | plantilla y script para sign-off manual controlado |
| PR-16 | Paquete consolidado de sign-off | ✅ Mergeado | consolidación de evidencia final en un solo artefacto |
| PR-17 | Workflow completo de sign-off | ✅ Mergeado | orquestación CI de checklist+paquete junto al release gate |
| PR-18 | Cierre formal de fase operativa | ✅ Mergeado | cierre documental de fase 5 completado con criterios consolidados |
| PR-19 | Orden documental y sync Outline idempotente | ✅ Mergeado | dedupe de Outline + estructura documental ordenada + script anti-duplicados |
| PR-20 | Estabilizar worker Synology (one-shot sin restart loop) | ✅ Mergeado | `worker.restart="no"` + operación Synology estable sin loop |
| PR-21 | Corrección documental post PR-19/PR-20 | ✅ Mergeado | roadmap/master-plan/runbook alineados + sync Outline validado |
| PR-22 | Retención y gobierno de artifacts | ✅ Mergeado | política 30/60/90 días + limpieza automática + trazabilidad auditable |
| PR-23 | Observabilidad y alerting de infraestructura | ✅ Mergeado | alertas operacionales + SLO de pipeline + workflow horario |
| PR-24 | Resiliencia, recuperación y hardening operacional | ✅ Mergeado | backup/restore + DR + hardening de secretos/permisos |
| PR-25 | Clasificador de régimen de mercado | ✅ Mergeado | clasificación de contexto de mercado para gating |
| PR-26 | Sizing dinámico por volatilidad/riesgo | ✅ Mergeado | position sizing adaptativo por riesgo cuantitativo |
| PR-27 | Riesgo de portafolio y correlación | ✅ Mergeado | límites de exposición multi-símbolo y correlación |
| PR-28 | Gate de decisión final y circuit breakers avanzados | ✅ Mergeado | capa final de decisión y apagado seguro |
| PR-29 | Router Binance Testnet | ✅ Mergeado | ejecución real en testnet con trazabilidad de órdenes |
| PR-30 | Reconciliación y máquina de estados de ejecución | ✅ Mergeado | consistencia entre órdenes/posiciones/eventos |
| PR-31 | Paridad paper vs testnet (shadow run) | ✅ Mergeado | reporte comparativo y brechas de comportamiento |
| PR-32 | Alerting y reporting de producción | ✅ Mergeado | resumen diario operativo y evaluación temprana de alertas |
| PR-33 | Backtesting y walk-forward | ✅ Mergeado | baseline cuantitativo reproducible con benchmark y walk-forward |
| PR-34 | Checklist de transición y rampa de capital | 🟡 En progreso | criterios formales para eventual salida de paper |
| PR-35 | Cutover controlado y monitoreo post-cutover | 🔵 Planificado | transición asistida con gates y rollback explícito |

## Secuencia de PRs actualizada

### PR-1 — Gobierno del repositorio y workflow por PR
**Estado:** ✅ Mergeado

**Objetivo**
Formalizar el carril de trabajo por Pull Requests.

**Entregables**
- `docs/pr-plan/PR_ROADMAP.md`
- `docs/pr-plan/PR_TEMPLATE_CHECKLIST.md`
- `.github/pull_request_template.md`
- actualización de runbook/README si aplica

---

### PR-2 — Ingesta inicial de mercado Binance
**Estado:** ✅ Mergeado

**Objetivo**
Capturar OHLCV básico y snapshot de mercado para alimentar al worker con datos reales.

**Entregables**
- cliente de market data
- modelos persistentes de snapshots / candles
- endpoint/scheduler mínimo
- docs + diagramas

---

### PR-3 — Hardening de ingesta de mercado
**Estado:** ✅ Mergeado

**Objetivo**
Endurecer la ingesta Binance y dejarla apta como base confiable para indicadores y señales.

**Entregables**
- correcciones de overflow
- control de concurrencia / deduplicación
- rollback explícito
- revisión semántica de Greptile incorporada

---

### PR-4 — Hardening post-merge de ingesta
**Estado:** ✅ Mergeado

**Objetivo**
Cerrar ajustes post-merge detectados durante la revisión de la capa de mercado sin perder trazabilidad por PR.

**Entregables**
- fixes puntuales post-merge
- test de idempotencia
- estabilización final de la capa de mercado

---

### PR-5 — Indicadores técnicos base
**Estado:** ✅ Mergeado

**Objetivo**
Implementar la primera capa de indicadores calculados sobre candles persistidos.

**Entregables**
- EMA
- RSI
- ATR
- momentum
- tests
- ADR-010

---

### PR-6 — Señales y features técnicos base
**Estado:** ✅ Mergeado

**Objetivo**
Construir la primera capa de señales derivadas sobre indicadores para preparar el worker market-driven.

**Entregables**
- `SignalService`
- `SignalSnapshot`
- endpoint `GET /signals/{symbol}`
- features semánticas (`trend_bias`, `momentum_bias`, `volatility_regime`, `ema_spread_pct`, `atr_pct`)
- ADR-011
- tests de señales base

---

### PR-7 — Worker market-driven
**Estado:** ✅ Mergeado

**Objetivo**
Reemplazar el loop demo estático por generación de trade plans basada en señales de mercado reales, manteniendo fallback demo cuando corresponda.

**Entregables**
- worker híbrido demo/market
- reglas de activación
- persistencia de señales/insights si aplica
- documentación

---

### PR-8 — Observabilidad y hardening operativo
**Estado:** ✅ Mergeado

**Objetivo**
Agregar salud operativa, métricas y controles de incidente.

**Entregables**
- métricas
- logs estructurados
- alertas
- eventos de riesgo ampliados
- documentación

---

### PR-9 — Despliegue real en Synology
**Estado:** ✅ Mergeado

**Objetivo**
Llevar el stack a contenedores reales dentro del NAS con smoke tests y runbook final.

**Entregables**
- build/deploy real
- verificación health
- validación endpoints
- validación dashboard
- smoke test automatizado (`scripts/synology_smoke_test.sh` + workflow `synology-smoke.yml`)
- runbook operativo final

**Gate extra**
No activar live trading. Solo deploy + smoke tests + paper/testnet.

---

### PR-10 — Preflight de configuración Synology
**Estado:** ✅ Mergeado

**Objetivo**
Agregar un gate previo al despliegue que valide configuración (`.env`) y resolución de `docker compose` antes de ejecutar build/up en NAS.

**Entregables**
- script `scripts/synology_preflight_check.sh`
- workflow manual `synology-preflight.yml`
- actualización de runbook/deployment/README
- ADR-014

**Gate extra**
Mantener `PAPER_TRADING=true` y no habilitar live trading.

---

### PR-11 — Release gate unificado Synology
**Estado:** ✅ Mergeado

**Objetivo**
Unificar en una sola corrida auditable el gate `preflight -> smoke`, con reporte formal para trazabilidad de operación.

**Entregables**
- script `scripts/synology_release_gate.sh`
- workflow manual `synology-release-gate.yml`
- reporte Markdown de resultados como artefacto
- docs/runbook actualizados para ejecución única

**Gate extra**
Sin live trading; solo operación controlada y validación de salud/despliegue.

---

### PR-12 — Resumen JSON y evidencia máquina-legible del gate
**Estado:** ✅ Mergeado

**Objetivo**
Transformar la salida del release gate en evidencia estructurada (JSON) para auditoría automática y trazabilidad en CI.

**Entregables**
- parser `scripts/synology_release_gate_summary.py`
- workflow `synology-release-gate.yml` con artifact JSON + job summary
- docs/runbook actualizados

**Gate extra**
Mantener `PAPER_TRADING=true` y no habilitar live trading.

### PR-13 — Verificación automática del JSON del gate
**Estado:** ✅ Mergeado

**Objetivo**
Validar automáticamente que el resumen JSON del release gate cumpla estructura esperada (`overall`, `steps`, `step_count`) y consistencia mínima.

**Entregables**
- script validador de `synology-release-gate.json`
- integración en workflow `synology-release-gate.yml`
- tests unitarios del validador
- ADR de criterio de validación

**Gate extra**
Sin live trading; validación solo de calidad/evidencia operativa.

---

### PR-14 — Atajos operativos con Makefile
**Estado:** ✅ Mergeado

**Objetivo**
Reducir fricción operacional con comandos estandarizados para ejecutar preflight/smoke/release gate sin repetir invocaciones largas.

**Entregables**
- `Makefile` con targets de operación Synology
- documentación de uso en README/runbook
- validación de targets en entorno local

**Gate extra**
Sin live trading; solo ergonomía operativa y consistencia de ejecución.

---

### PR-15 — Checklist de aprobación operacional
**Estado:** ✅ Mergeado

**Objetivo**
Estandarizar la evidencia de aprobación humana posterior al gate automático mediante una checklist operacional reproducible.

**Entregables**
- script `scripts/synology_release_checklist.py`
- target Make `synology-release-checklist`
- documentación de uso en README/runbook
- ADR de criterio de sign-off manual

**Gate extra**
No habilita live trading; formaliza aprobación manual para operación controlada.

---

### PR-16 — Paquete consolidado de sign-off
**Estado:** ✅ Mergeado

**Objetivo**
Consolidar la evidencia final del ciclo operativo en un solo artefacto Markdown para auditoría/handoff.

**Entregables**
- script `scripts/synology_signoff_package.py`
- target Make `synology-signoff-package`
- tests del empaquetador
- ADR-020

**Gate extra**
Sin live trading; consolida evidencia del modo controlado.

---

### PR-17 — Workflow completo de sign-off
**Estado:** ✅ Mergeado

**Objetivo**
Automatizar en CI la generación de checklist y paquete final de sign-off dentro del workflow de release gate.

**Entregables**
- actualización de `synology-release-gate.yml`
- parámetros de sign-off (`signoff_owner`, `signoff_notes`)
- artifacts extendidos (`checklist` + `signoff-package`)
- docs/runbook de ejecución completa

**Gate extra**
Sin live trading; automatización solo de evidencia operativa.

---

### PR-18 — Cierre formal de fase operativa
**Estado:** ✅ Mergeado

**Objetivo**
Cerrar formalmente la fase 5 con documento de cierre, checklist de criterios cumplidos y recomendaciones de continuidad.

**Entregables**
- `docs/plans/phase5-operational-closure.md`
- actualización de roadmap/gantt a estado de fase completada
- actualización de runbook con referencia al cierre

**Gate extra**
Mantener guardrails de paper trading y no habilitar live trading.

---

### PR-19 — Orden documental y sync Outline idempotente
**Estado:** ✅ Mergeado

**Objetivo**
Eliminar duplicados en Outline, ordenar la navegación documental y dejar automatizado un sync idempotente para evitar reincidencias.

**Entregables**
- `scripts/sync_outline_docs.py` (upsert + dedupe + estructura por categorías)
- `docs/README.md` e índices por carpeta (`docs/adr|plans|diagrams|pr-plan/README.md`)
- resolución del conflicto de numeración moviendo `ADR-008-market-ingestion-foundation.md` a `docs/adr/archive/`
- runbook/README actualizados con proceso de sync sin duplicados

**Gate extra**
No modifica lógica de trading; sólo gobernanza y orden documental.

---

### PR-20 — Estabilizar worker Synology (one-shot sin restart loop)
**Estado:** ✅ Mergeado

**Objetivo**
Eliminar reinicios infinitos del worker en Synology y alinear operación con su naturaleza one-shot.

**Entregables**
- `infra/docker/synology/docker-compose.yml` con `worker.restart: "no"`
- confirmación operativa en NAS: servicios persistentes (`api/web/postgres/redis`) + jobs one-shot (`migrate/worker`)

---

### PR-21 — Corrección documental post PR-19/PR-20
**Estado:** ✅ Mergeado

**Objetivo**
Alinear documentación estratégica y operativa con la implementación real en Synology.

**Entregables**
- actualización de roadmap + PR roadmap + master plan + runbook
- sincronización de Outline validada (`docs_synced=42`)

---

### PR-22 — Retención y gobierno de artifacts
**Estado:** ✅ Mergeado

**Objetivo**
Controlar crecimiento de evidencia operativa y conservar sólo la historia útil para auditoría.

**Entregables**
- script `scripts/synology_artifact_retention.py`
- target Make `synology-artifact-retention`
- workflow `Synology Artifact Retention` (dispatch + schedule)
- política 30/60/90 días y reporte JSON por corrida

---

### PR-23 — Observabilidad y alerting de infraestructura
**Estado:** ✅ Mergeado

**Objetivo**
Convertir fallos operativos en señales accionables antes de que impacten continuidad.

**Entregables**
- script `scripts/synology_operational_observability.py`
- workflow `Synology Observability & Alerting` (dispatch + schedule horario)
- target Make `synology-operational-observability`
- reporte JSON + resumen Markdown (`artifacts/synology-operational-observability.*`)
- ADR-024 de observabilidad operacional

---

### PR-24 — Resiliencia, recuperación y hardening operacional
**Estado:** ✅ Mergeado

**Objetivo**
Asegurar continuidad ante incidentes y reducir riesgo por exposición operativa.

**Entregables**
- script `scripts/synology_resilience_backup.py` (bundle + manifest + verify-restore)
- target Make `synology-resilience-backup`
- workflow `Synology Resilience Backup Verify` (dispatch + schedule diario)
- ADR-025 + runbook con baseline RTO/RPO y evidencia operacional
- inventario/rotación de secretos y revisión de superficie expuesta (siguiente iteración del PR)

---

### PR-25 — Clasificador de régimen de mercado
**Estado:** ✅ Mergeado

**Objetivo**
Diferenciar contexto de mercado para ajustar reglas de entrada/salida y riesgo.

**Entregables**
- clasificador de régimen
- señales de contexto integradas al gating
- tests y ADR de criterio de clasificación

---

### PR-26 — Sizing dinámico por volatilidad/riesgo
**Estado:** ✅ Mergeado

**Objetivo**
Escalar tamaño de posición según volatilidad y presupuesto de riesgo.

**Entregables**
- módulo de sizing dinámico
- límites por símbolo/escenario
- evidencia de sensibilidad en tests

---

### PR-27 — Riesgo de portafolio y correlación
**Estado:** ✅ Mergeado

**Objetivo**
Evitar sobreexposición agregada por posiciones correlacionadas.

**Entregables**
- matriz/cálculo de correlación operativa
- límites agregados multi-símbolo
- eventos de riesgo enriquecidos

---

### PR-28 — Gate de decisión final y circuit breakers avanzados
**Estado:** ✅ Mergeado

**Objetivo**
Consolidar una capa final de autorización/rechazo de trade plan.

**Entregables**
- gate final con score compuesto
- circuit breakers avanzados
- trazabilidad de razones de bloqueo

---

### PR-29 — Router Binance Testnet
**Estado:** ✅ Mergeado

**Objetivo**
Conectar ejecución a Binance Testnet manteniendo control y trazabilidad completos.

**Entregables**
- router de órdenes testnet
- manejo de errores/reintentos/idempotencia base
- pruebas de integración en testnet

---

### PR-30 — Reconciliación y máquina de estados de ejecución
**Estado:** ✅ Mergeado

**Objetivo**
Alinear estado interno del bot con estado real de órdenes/posiciones del exchange.

**Entregables**
- state machine de ejecución
- reconciliación periódica de órdenes/posiciones
- reporte de drift operacional

---

### PR-31 — Paridad paper vs testnet (shadow run)
**Estado:** ✅ Mergeado

**Objetivo**
Medir brecha entre comportamiento esperado (paper) y real (testnet) antes de cualquier transición.

**Entregables**
- corrida shadow comparativa
- reporte de desvíos por estrategia
- criterios de aceptación mínimos para avanzar

---

### PR-32 — Alerting y reporting de producción
**Estado:** 🟡 En progreso

**Objetivo**
Agregar una capa mínima de visibilidad operativa diaria para detectar degradación temprana antes de la etapa formal de go-live readiness.

**Entregables**
- servicio `ProductionReportingService`
- endpoint `GET /reporting/daily-summary`
- endpoint `GET /alerts/evaluate`
- ADR-033
- tests unitarios y de rutas para reporting/alertas

---

### PR-33 — Backtesting y walk-forward
**Estado:** 🟡 En progreso

**Objetivo**
Validar robustez estadística de estrategias bajo distintos periodos y condiciones.

**Entregables**
- framework de backtest/walk-forward
- métricas de rendimiento y riesgo
- benchmark `buy_and_hold` comparable
- endpoint `POST /backtesting/run`
- ADR-034
- informe técnico reproducible

---

### PR-34 — Checklist de transición y rampa de capital
**Estado:** 🔵 Planificado

**Objetivo**
Definir formalmente condiciones para eventual transición fuera de paper.

**Entregables**
- checklist de transición go/no-go
- política de rampa de capital por etapas
- plan de rollback por umbrales de pérdida

---

### PR-35 — Cutover controlado y monitoreo post-cutover
**Estado:** 🔵 Planificado

**Objetivo**
Ejecutar transición asistida únicamente si todos los gates anteriores se cumplen.

**Entregables**
- plan de cutover con pasos verificables
- monitoreo intensivo post-cutover
- criterio de rollback inmediato y comunicación de incidente

## Criterio de avance
No abrir el siguiente PR como “en progreso” hasta dejar el anterior con:
- checks terminados
- documentación actualizada
- comentarios/reviews resueltos
- estado consolidado en memoria
- roadmap y Gantt actualizados
