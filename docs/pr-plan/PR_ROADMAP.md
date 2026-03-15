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
| PR-34 | Checklist de transición y rampa de capital | ✅ Mergeado | criterios formales para eventual salida de paper |
| PR-35 | Cutover controlado y monitoreo post-cutover | ✅ Mergeado | transición asistida con gates y rollback explícito |
| PR-36 | Drills sintéticos y paquete de evidencia de cutover | ✅ Mergeado | ensayos controlados y artifacts previos al cutover real |
| PR-37 | Templates operativos de artefactos de cutover | ✅ Mergeado | plantillas reutilizables para reportes, incidentes y cierre |
| PR-38 | Links navegables para documentación sincronizada en Outline | ⚪ Cerrado | continuidad absorbida por PR-39 tras renombre de rama |
| PR-39 | Links navegables para documentación sincronizada en Outline | ✅ Mergeado | reescritura de links locales a Outline/GitHub durante el sync + sync Outline validado (`docs_synced=59`) |
| PR-40 | Validación CI de links Markdown documentales | ✅ Mergeado | lint/test de links locales para prevenir regresiones antes del sync a Outline |
| PR-41 | Gate auditable de shadow run para readiness testnet | ✅ Mergeado | reporte/API/workflow para evaluar Gate C con evidencia JSON+Markdown ya desplegado en Synology |
| PR-42 | Activación de shadow run testnet en Synology | ✅ Mergeado | credenciales cargadas y primer gate útil con `testnet_executed > 0` |
| PR-43 | Normalización de fills testnet y reconciliación | ✅ Mergeado | fills testnet normalizados + shadow run limpio con `fill_rate=100%` |
| PR-44 | Guard de reconciliación para órdenes rechazadas históricas | ✅ Mergeado | follow-up de review para no inflar fills con rechazos heredados |
| PR-45 | Centro de mando operacional | ✅ Mergeado | endpoint agregado + UI rica para mostrar operaciones, órdenes, posiciones, riesgo y shadow run |
| PR-46 | Radar unificado por operación en el centro de mando | ✅ Mergeado | vista consolidada por trade plan con setup, orden, posición, reconcile y riesgo |
| PR-47 | Línea de tiempo operativa unificada | ✅ Mergeado | feed cronológico plan→orden→posición→riesgo→reconcile en el dashboard |
| PR-48 | Drill-down por trade plan en el centro de mando | ✅ Mergeado | ficha detallada por operación con anchors y mini-timeline asociada |
| PR-49 | Justificación técnica por trade plan en el centro de mando | ✅ Mergeado | scores, régimen, timeframe y tesis visibles por operación |
| PR-50 | UX de entry real / delta vs plan en el command center | ✅ Mergeado | estados sin ejecución real ahora muestran `—` en vez de falsos `+0.000%` |
| PR-51 | Persistencia de fill real desde Binance | ✅ Mergeado | refresh post-submit contra Binance Testnet + persistencia del fill real + cierre total de reviews |
| PR-52 | Hardening residual del refresh testnet | 🟡 En progreso | evitar refresh innecesario para `partially_filled` completo y blindar `orderId` falsy en el fallback a `clientOrderId` |

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
**Estado:** ✅ Mergeado

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
**Estado:** ✅ Mergeado

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
**Estado:** ✅ Mergeado

**Objetivo**
Definir formalmente condiciones para eventual transición fuera de paper.

**Entregables**
- checklist de transición go/no-go
- política de rampa de capital por etapas
- plan de rollback por umbrales de pérdida

---

### PR-35 — Cutover controlado y monitoreo post-cutover
**Estado:** ✅ Mergeado

**Objetivo**
Ejecutar transición asistida únicamente si todos los gates anteriores se cumplen.

**Entregables**
- plan de cutover con pasos verificables
- monitoreo intensivo post-cutover
- criterio de rollback inmediato y comunicación de incidente

---

### PR-36 — Drills sintéticos y paquete de evidencia de cutover
**Estado:** ✅ Mergeado

**Objetivo**
Formalizar ensayos previos al cutover real y estandarizar la evidencia obligatoria de ejecución/rollback.

**Entregables**
- catálogo mínimo de drills sintéticos
- paquete de evidencia estándar de cutover
- criterio de aprobación/rechazo del ensayo

---

### PR-37 — Templates operativos de artefactos de cutover
**Estado:** ✅ Mergeado

**Objetivo**
Bajar el contrato documental a templates reutilizables para operación real y drills repetibles.

**Entregables**
- templates operativos para reporte inicial (Markdown + JSON), incident log, drill results y closeout
- referencias desde el plan de drills hacia templates concretos
- ADR-038

---

### PR-38 — Links navegables para documentación sincronizada en Outline
**Estado:** ⚪ Cerrado

**Objetivo**
Intento inicial de continuidad para la reescritura de links locales, cerrado al renombrar la rama fuente.

**Entregables**
- continuidad absorbida por `PR-39`

---

### PR-39 — Links navegables para documentación sincronizada en Outline
**Estado:** ✅ Mergeado

**Objetivo**
Evitar que Outline publique links locales/rotos, reescribiéndolos a URLs navegables del documento equivalente en Outline o al repositorio web.

**Entregables**
- reescritura automática de links relativos/locales en `scripts/sync_outline_docs.py`
- fallback estable a GitHub `blob/<ref>`
- documentación operativa de la estrategia de links
- ADR-039
- sync post-merge validado (`docs_synced=59`, `duplicates_archived=0`, `unknown_archived=0`)

### PR-40 — Validación CI de links Markdown documentales
**Estado:** ✅ Mergeado

**Objetivo**
Prevenir regresiones documentales antes del sync a Outline validando en CI que los links locales Markdown resuelvan correctamente dentro del repo.

**Entregables**
- script `scripts/check_markdown_links.py`
- tests focales para parser/casos válidos/rotos
- job `docs-links` en CI
- actualización de roadmap/runbook según corresponda

### PR-41 — Gate auditable de shadow run para readiness testnet
**Estado:** ✅ Mergeado

**Objetivo**
Automatizar la evidencia del Gate C (paridad paper vs testnet) para decidir si el bot está listo para comenzar shadow run serio y aproximarse a real-micro con criterios medibles.

**Entregables**
- `ShadowRunReportingService` + endpoint `GET /reporting/shadow-run-summary`
- esquema de salida consolidado para duración/volumen/paridad/fill-rate/slippage/incidentes
- script `scripts/synology_shadow_run_gate.py` para generar artefactos JSON + Markdown
- workflow `.github/workflows/synology-shadow-run-gate.yml`
- ADR-040 + actualización de roadmap/runbook/checklist de transición
- mergeado en `d486e63` + deploy validado en Synology
- primer gate real ejecutado: `paper=63`, `testnet=0`, `duration_days=3.0494`, `overall=FAIL`

### PR-42 — Activación de shadow run testnet en Synology
**Estado:** ✅ Mergeado

**Objetivo**
Desbloquear la primera ventana útil de shadow run testnet en Synology corrigiendo la configuración real del NAS (credenciales Binance testnet y variables operativas faltantes) y re-ejecutando el Gate C con datos testnet genuinos.

**Entregables**
- documentación explícita del bloqueo operativo real detectado en NAS (`BINANCE_API_KEY`/`BINANCE_API_SECRET` vacíos)
- guía/ajuste para `SYNOLOGY_API_BASE_URL` y ejecución remota del workflow
- evidencia del primer rerun del Gate C tras habilitar testnet
- mergeado en `bebf3bb` + sync Outline `docs_synced=60`
- estado real posterior: 3 ejecuciones `testnet_executed` iniciales (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`)

### PR-43 — Normalización de fills testnet y reconciliación
**Estado:** ✅ Mergeado

**Objetivo**
Corregir el falso drift crítico cuando Binance Testnet devuelve órdenes con `status=new` pero `executedQty > 0`, de modo que la persistencia y la reconciliación reflejen fills reales.

**Entregables**
- normalización de estado en `BinanceTestnetTradingService`
- reconciliación robusta basada también en `executed_quantity`
- tests para órdenes `NEW` con ejecución efectiva
- mergeado en `a85c305`

### PR-44 — Guard de reconciliación para órdenes rechazadas históricas
**Estado:** ✅ Mergeado

**Objetivo**
Evitar que la reconciliación clasifique como fill órdenes rechazadas heredadas de versiones previas que pudieron quedar con `executed_quantity > 0` por un bug histórico.

**Entregables**
- exclusión explícita de estados terminales de fallo en `filled_orders`
- test focal para orden `rejected` con `executed_quantity > 0`
- ajuste adicional post-review: `canceled/cancelled/expired` con `executed_quantity > 0` siguen contando como fill parcial legítimo
- mergeado en `f0c0015`

### PR-45 — Centro de mando operacional
**Estado:** ✅ Mergeado

**Objetivo**
Mostrar en la UI del centro de mando toda la información relevante de operación en tiempo real práctico: planes, órdenes, posiciones, eventos de riesgo, reconciliación y snapshot de shadow run, sin depender de múltiples endpoints manuales.

**Entregables**
- endpoint agregado `GET /dashboard/command-center`
- servicio backend con snapshot operativo unificado
- home de `apps/web` rediseñada para mostrar operaciones recientes, órdenes, posiciones, riesgo y readiness testnet
- tests de servicio/ruta + build frontend verde
- mergeado y desplegado en Synology

### PR-46 — Radar unificado por operación en el centro de mando
**Estado:** ✅ Mergeado

**Objetivo**
Subir la granularidad del centro de mando consolidando por operación el plan, la orden, la posición, la reconciliación y el último evento de riesgo en una sola vista operativa.

**Entregables**
- `operation_snapshots` en `GET /dashboard/command-center`
- tabla “Radar de operaciones” con setup, orden, posición, reconcile y riesgo por trade plan
- tests de servicio/ruta + build frontend verde
- mergeado en `4285d30` y desplegado en Synology

### PR-47 — Línea de tiempo operativa unificada
**Estado:** ✅ Mergeado

**Objetivo**
Mostrar cronológicamente en el centro de mando el flujo de cada operación (creación de plan, orden, posición, riesgo y drift) para entender qué pasó y cuándo sin saltar entre widgets.

**Entregables**
- `timeline` en `GET /dashboard/command-center`
- feed visual “Línea de tiempo operativa” en la home del dashboard
- tests de servicio/ruta + build frontend verde
- mergeado en `722b49f` y desplegado en Synology

### PR-48 — Drill-down por trade plan en el centro de mando
**Estado:** ✅ Mergeado

**Objetivo**
Permitir leer cada operación reciente como una ficha autosuficiente con setup, ejecución, salud y timeline asociada, evitando reconstruir contexto manualmente desde varias tablas.

**Entregables**
- sección “Detalle por trade plan” en la home del dashboard
- enlaces desde radar/timeline al bloque detallado del trade plan
- timeline asociada por operación dentro de cada ficha
- build frontend verde
- mergeado en `8d3d9d5` y desplegado en Synology

### PR-50 — Justificación técnica por orden en el centro de mando
**Estado:** ✅ Mergeado

**Objetivo**
Mostrar para cada operación la justificación técnica persistida (scores, régimen, timeframe y tesis) y separar explícitamente el dato que sí existe hoy del dato que aún no se persiste (snapshots crudos de indicadores/patrones).

**Entregables**
- scores `technical/fundamental/sentiment/confidence/aggregate` visibles en la ficha del trade plan
- `thesis` visible en el dashboard
- aclaración explícita de limitación actual sobre RSI/MACD/EMA/patrones no persistidos por trade plan
- tests de servicio/ruta + build frontend verde
- mergeado / deploy en curso o siguiente turno de despliegue

### PR-51 — Persistencia de fill real desde Binance
**Estado:** ✅ Mergeado

**Objetivo**
Confirmar la orden contra Binance Testnet después del submit y persistir el fill real del exchange, evitando que el sistema siga cayendo al precio planificado cuando el primer payload viene incompleto.

**Entregables**
- `get_order` en cliente Binance para refresco post-orden
- `_confirm_exchange_order()` + `_extract_fill_price()` en `BinanceTestnetTradingService`
- derivación de precio real desde `avgPrice`, `price` o `cumQuote / executedQty`
- tests del servicio para refresh y cálculo de fill real
- mergeado en `6c0b632` tras resolver todos los comments de Greptile/Codex y cerrar el último borde de `unknown_status`

### PR-52 — Hardening residual del refresh testnet
**Estado:** 🟡 En progreso

**Objetivo**
Cerrar dos bordes residuales del refresh post-submit para reducir ruido hacia Binance Testnet y blindar el fallback por `clientOrderId` cuando `orderId` llega como valor falsy.

**Entregables**
- no refrescar órdenes `PARTIALLY_FILLED` cuando ya traen `avgPrice` y `executedQty` válidos
- usar `clientOrderId` como identificador efectivo cuando `orderId` llegue falsy (`0`, `""`, `False`)
- tests específicos para ambos escenarios
- actualización de roadmap y sync de Outline post-PR

## Criterio de avance
No abrir el siguiente PR como “en progreso” hasta dejar el anterior con:
- checks terminados
- documentación actualizada
- comentarios/reviews resueltos
- estado consolidado en memoria
- roadmap y Gantt actualizados

---
