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
11. **Regla Greptile de oro:** leer siempre resumen + comentarios; resolver cada comentario antes de merge. Se puede mergear con `Confidence Score` **4/5 o 5/5** si no hay blockers reales; cualquier deuda técnica remanente debe quedar documentada como follow-up.

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
| PR-49 | Aclarar entry planificada vs entry real en el centro de mando | ⚪ Cerrado | branch fallido/superado; su intención quedó absorbida por cambios posteriores sin mergearlo |
| PR-50 | Justificación técnica por orden en el centro de mando | ✅ Mergeado | scores, régimen, timeframe y tesis visibles por operación |
| PR-51 | Persistencia de fill real desde Binance | ✅ Mergeado | refresh post-submit contra Binance Testnet + persistencia del fill real + cierre total de reviews |
| PR-52 | Hardening residual del refresh testnet | ✅ Mergeado | evita refresh innecesario en `PARTIALLY_FILLED` completos y blinda fallback por `clientOrderId` |
| PR-53 | Historial operativo completo por `trade_plan_id` | ✅ Mergeado | historial end-to-end por operación + reconcile visible + payload endurecido post-review |
| PR-54 | Smoke Synology del command center enriquecido | ✅ Mergeado | smoke script endurecido para `/dashboard/command-center` + runbook actualizado + validación real en NAS |
| PR-55 | Deduplicar fetch web del smoke Synology | ✅ Mergeado | una sola descarga de `${WEB_BASE_URL}/` + validación múltiple de marcadores sobre el mismo HTML |
| PR-56 | Evidencia operativa del command center para shadow run gate | ✅ Mergeado | artifact JSON/Markdown del gate incorpora snapshot operacional del command center |
| PR-57 | Alinear docs del gate con evidencia del command center | ✅ Mergeado | runbook + checklist + ADR-040 actualizados para exigir/referenciar el bloque `command_center` |
| PR-58 | Persistir y backfillear precios reales desde Binance | ✅ Mergeado | usar `userTrades` como fuente de fill real y corregir órdenes/posiciones testnet ya abiertas |
| PR-59 | Bloquear ejecución testnet desde señales demo | ✅ Mergeado | impedir que `source=demo` dispare órdenes reales en Binance Testnet |
| PR-60 | Auto-ingestar mercado antes de caer a demo | ✅ Mergeado | si faltan candles/snapshot, el worker intenta `POST /market/ingest/{symbol}` y reintenta el setup market-driven |
| PR-61 | Normalizar cantidad testnet para Binance | ✅ Mergeado | serialización limpia de quantity para evitar `400 Bad Request` por artefactos float |
| PR-62 | Hardening fino del serializer de quantity | ✅ Mergeado | rechazar `NaN` / infinitos y completar la cobertura del serializer de quantity |
| PR-63 | Metadata estructurada para `risk_events` | ✅ Mergeado | agregar contexto JSON auditable a errores/eventos críticos para acelerar debugging operativo |
| PR-64 | Hacer visible `risk_events.context_json` en el command center | ✅ Mergeado | renderizar la metadata estructurada de eventos en la UI para debugging y postmortems más rápidos |
| PR-65 | Resumen contextual del último riesgo por operación | ✅ Mergeado | exponer y renderizar `latest_risk_context` en la vista resumida del command center |
| PR-66 | Smoke Synology para contexto de riesgo | ✅ Mergeado | validar por smoke automatizado los nuevos marcadores/contextos del command center en API y UI, con gating condicional para payloads limpios |
| PR-67 | Cobertura testeable del smoke para contexto | ✅ Mergeado | extraer la validación del smoke a helper testeable y cubrir payload limpio vs payload con contexto |
| PR-68 | Manejo limpio de errores CLI del helper de smoke | ✅ Mergeado | capturar errores del entrypoint con mensajes claros en stderr y tests reproducibles de fallo |
| PR-69 | Fixtures locales para el shell smoke | ✅ Mergeado | cubrir `synology_smoke_test.sh` end-to-end con servidor fixture local y gating HTML reproducible |
| PR-70 | Cierre formal de Fase 14 + hardening final del fixture shell | ✅ Mergeado | tipado explícito, teardown determinista y cierre formal de la fase de observabilidad |
| PR-71 | Cobertura shell para payload inválido del command center | ✅ Mergeado | validar end-to-end que el shell smoke falla cuando el payload API rompe el contrato del helper |
| PR-72 | Cobertura shell para fallos HTTP base | ✅ Mergeado | validar con fixture local que `/health` y `/metrics` rompen el smoke con errores claros |
| PR-73 | Cobertura shell para summary y trade-plans | ✅ Mergeado | validar con fixture local que `/dashboard/summary` y `/trade-plans` rompen el smoke con errores claros |
| PR-74 | `/metrics` autenticado + cleanup de helpers del fixture | ✅ Mergeado | cubrir header auth de métricas y reducir duplicación menor del fixture shell |
| PR-75 | Cobertura shell para strictness de `testnet/ping` | ✅ Mergeado | cubrir branches `STRICT_EXTERNAL_CHECKS=true/false` para `testnet/ping` con fixture local reproducible |
| PR-76 | Failure modes de `WEB /` en el shell smoke | ✅ Mergeado | cubrir `WEB /` non-200 y `WEB /` con body vacío con fixture local reproducible |
| PR-77 | Marcadores faltantes de `WEB /` en el shell smoke | ✅ Mergeado | cubrir respuestas `200` de `WEB /` sin marcadores base/centrales del dashboard con fixture local reproducible |
| PR-78 | Marcadores adicionales de `WEB /` en el shell smoke | ✅ Mergeado | cubrir respuestas `200` de `WEB /` sin `Detalle por trade plan` o `Reconcile actual` con fixture local reproducible |
| PR-79 | Marcadores restantes de órdenes y posiciones en el shell smoke | ✅ Mergeado | cubrir respuestas `200` de `WEB /` sin `Historial de órdenes` o `Historial de posiciones` con fixture local reproducible |
| PR-80 | Cierre formal de Fase 15 | ✅ Mergeado | consolidar el cierre documental del hardening del harness operacional y devolver el foco del roadmap a producto/trading |
| PR-81 | Sincronizar resumen del roadmap tras cierre de Fase 15 | ✅ Mergeado | alinear el resumen ejecutivo del roadmap con el estado real tras el cierre formal del carril de harness |
| PR-82 | Emparejamiento shadow run sensible a timeframe | ✅ Mergeado | evitar cruces paper/testnet entre trade plans del mismo símbolo/lado pero distinta temporalidad |
| PR-83 | Execution parity sensible a timeframe | ✅ Mergeado | alinear el reporte puntual de parity con la misma regla de `timeframe` usada en shadow run |
| PR-84 | Sincronizar roadmap tras baseline de Etapa N | ✅ Mergeado | dejar consistente el estado documental tras el merge de PR-83 y pausar follow-ups de parity no urgentes |
| PR-85 | Sincronizar docs tras merge de PR-84 | ✅ Mergeado | cerrar el último desfase documental residual tras el merge de PR-84 |
| PR-86 | Filtro por timeframe en execution parity | ✅ Mergeado | permitir consultar `/execution/parity/{symbol}` por temporalidad sin mezclar múltiples timeframes en un mismo reporte |
| PR-87 | Filtro por timeframe en shadow-run-summary | ✅ Mergeado | permitir consultar el resumen agregado de shadow run por temporalidad sin mezclar múltiples timeframes en un mismo snapshot |
| PR-88 | Breakdown por timeframe en shadow-run symbols | ✅ Mergeado | evitar que `symbols` agregue bajo una sola fila reportes de un mismo símbolo que pertenecen a temporalidades distintas |
| PR-89 | Cierre formal de baseline de Etapa N | ✅ Mergeado | consolidar documentalmente la baseline inicial de parity/shadow run sensible a `timeframe` y devolver el foco a producto/trading |
| PR-90 | Sincronizar docs tras merge de PR-89 | ✅ Mergeado | cerrar el desfase documental residual y dejar el roadmap en estado post-Etapa N sin PRs activos |
| PR-91 | Shell modular del command center | 🟡 En progreso | transformar el homepage monolítico en una trading workstation modular con navegación clara y drill-down por operación |


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

### PR-49 — Aclarar entry planificada vs entry real en el centro de mando
**Estado:** ⚪ Cerrado (superado)

**Objetivo**
Distinguir visualmente `entry planificada` vs `entry real` dentro del drill-down operativo.

**Resultado**
- el branch quedó con `web-build` rojo y errores reales de compilación
- no se mergeó
- su intención funcional quedó absorbida por la secuencia posterior del command center (`PR-50`/`PR-51`), por lo que se cerró explícitamente para limpiar ruido histórico

### PR-50 — Justificación técnica por orden en el centro de mando
**Estado:** ✅ Mergeado

**Objetivo**
Mostrar para cada operación la justificación técnica persistida (scores, régimen, timeframe y tesis) y separar explícitamente el dato que sí existe hoy del dato que aún no se persiste (snapshots crudos de indicadores/patrones).

**Entregables**
- scores `technical/fundamental/sentiment/confidence/aggregate` visibles en la ficha del trade plan
- `thesis` visible en el dashboard
- aclaración explícita de limitación actual sobre RSI/MACD/EMA/patrones no persistidos por trade plan
- tests de servicio/ruta + build frontend verde
- mergeado en `7ae60a9`

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
**Estado:** ✅ Mergeado

**Objetivo**
Cerrar dos bordes residuales del refresh post-submit para reducir ruido hacia Binance Testnet y blindar el fallback por `clientOrderId` cuando `orderId` llega como valor falsy.

**Entregables**
- no refrescar órdenes `PARTIALLY_FILLED` cuando ya traen `avgPrice` y `executedQty` válidos
- usar `clientOrderId` como identificador efectivo cuando `orderId` llegue falsy (`0`, `""`, `False`)
- tests específicos para ambos escenarios
- actualización de roadmap + sync de Outline post-merge
- mergeado en `2f8293c` con `Greptile 5/5`

### PR-53 — Historial operativo completo por `trade_plan_id`
**Estado:** ✅ Mergeado

**Objetivo**
Profundizar el command center para que cada trade plan permita inspección end-to-end de órdenes, posiciones, risk events y timeline relacionada sin reconstrucción manual.

**Entregables**
- payload enriquecido por `trade_plan_id` en `/dashboard/command-center`
- UI detallada para historial operativo completo por operación
- métricas/acciones de reconcile visibles por operación
- mergeado en `f5368c8` tras cierre completo de reviews Greptile

### PR-54 — Smoke Synology del command center enriquecido
**Estado:** ✅ Mergeado

**Objetivo**
Convertir la validación manual post-PR-53 en una verificación repetible y auditable dentro del smoke Synology, para detectar drift entre API/UI y el entorno real del NAS.

**Entregables**
- `scripts/synology_smoke_test.sh` valida `GET /dashboard/command-center` y los marcadores UI del command center enriquecido
- runbook Synology actualizado con criterio mínimo de aprobación específico para el dashboard enriquecido
- validación real sobre NAS (`http://192.168.0.8:8010` / `http://192.168.0.8:3012`) documentada en el PR
- mergeado en `eefaa74` con `Greptile 4/5`

### PR-55 — Deduplicar fetch web del smoke Synology
**Estado:** ✅ Mergeado

**Objetivo**
Eliminar la redundancia del smoke web para que la home del dashboard se descargue una sola vez y todos los marcadores UI se validen sobre el mismo HTML, reduciendo tráfico y oportunidades de fallo transitorio.

**Entregables**
- helper de fetch único para `${WEB_BASE_URL}/`
- validación múltiple de marcadores sobre el mismo body HTML
- revalidación del smoke completo sobre el NAS real
- mergeado en `6f2bdb5`

### PR-56 — Evidencia operativa del command center para shadow run gate
**Estado:** ✅ Mergeado

**Objetivo**
Enriquecer el artifact auditable del shadow run con una instantánea operacional del command center, para que el gate no entregue solo métricas agregadas sino también contexto visible de las operaciones recientes.

**Entregables**
- `scripts/synology_shadow_run_gate.py` consulta también `/dashboard/command-center`
- artifact JSON incluye bloque `command_center`
- artifact Markdown agrega sección de evidencia operativa con top operaciones recientes y estado de reconcile
- mergeado en `1850eec`

### PR-57 — Alinear docs del gate con evidencia del command center
**Estado:** ✅ Mergeado

**Objetivo**
Hacer explícito en runbook, checklist y ADR que el gate auditable del shadow run ya no es solo cuantitativo: también incorpora contexto operacional del command center y debe revisarse como parte de la evidencia mínima.

**Entregables**
- `synology-runbook.md` exige revisar bloque `command_center` del artifact
- `transition-checklist-and-capital-ramp.md` pide evidencia operacional reciente dentro del gate
- `ADR-040` refleja la evolución del artifact hacia evidencia cuantitativa + operacional
- mergeado en `bbf0248`

### PR-58 — Persistir y backfillear precios reales desde Binance
**Estado:** ✅ Mergeado

**Objetivo**
Eliminar los precios ficticios del command center usando la fuente correcta de fill real (`userTrades`) y corregir también las órdenes/posiciones testnet ya abiertas que quedaron persistidas con precio planificado.

**Entregables**
- `BinanceFuturesClient.get_order_trades()` para recuperar fills reales por `orderId`
- `BinanceTestnetTradingService` persiste `order.price` / `position.entry_price` desde `userTrades`
- script `scripts/backfill_testnet_fill_prices.py` corrige registros testnet existentes en Postgres/NAS
- validación en NAS contra posiciones reales abiertas (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`)
- mergeado en `db51dbb`

### PR-59 — Bloquear ejecución testnet desde señales demo
**Estado:** ✅ Mergeado

**Objetivo**
Evitar que el worker ejecute órdenes reales en Binance Testnet cuando el setup provenga del fallback demo (`source=demo`, típicamente por `snapshot_incompleto`).

**Entregables**
- `process_symbol()` bloquea ejecución testnet si `meta.source != "market"`
- opcionalmente cae a paper trading si `TESTNET_FALLBACK_TO_PAPER=true`
- tests cubren bloqueo de ejecución real y fallback a paper
- despliegue del worker actualizado en Synology para cortar nuevas ejecuciones distorsionadas
- mergeado en `ea19847`

### PR-60 — Auto-ingestar mercado antes de caer a demo
**Estado:** ✅ Mergeado

**Objetivo**
Atacar la raíz de `snapshot_incompleto` en Synology: si faltan candles/snapshot en la DB, el worker debe intentar ingestar mercado y reintentar el setup market-driven antes de caer al fallback demo.

**Entregables**
- `TradingBotApiClient.ingest_market()`
- `HybridSignalService` reintenta tras `POST /market/ingest/{symbol}` cuando faltan snapshot/candles o el snapshot viene incompleto
- tests cubren recuperación por ingesta para `market_snapshot_missing` y `snapshot_incompleto`
- validación en NAS: logs del worker muestran nuevas corridas `source="market"`, `reason="ok"` para BTC/ETH/SOL tras auto-ingesta
- mergeado en `3d2b5a1`

### PR-61 — Normalizar cantidad testnet para Binance
**Estado:** ✅ Mergeado

**Objetivo**
Eliminar rechazos `400 Bad Request` por serialización sucia de cantidades (`0.8100000000000001`, `18.0300000000000011`) al enviar órdenes market a Binance Testnet.

**Entregables**
- serialización de quantity con precisión estable y sin artefactos float
- tests para `0.81` / `18.03`
- validación en NAS reintentando ETH/SOL sin rechazo por precisión
- mergeado en `535c108`

### PR-62 — Hardening fino del serializer de quantity
**Estado:** ✅ Mergeado

**Objetivo**
Cerrar deuda técnica menor del serializer de `quantity`: rechazar explícitamente `NaN` / infinitos y dejar la cobertura de errores usando `pytest.raises`.

**Entregables**
- `_serialize_quantity()` rechaza `NaN` / infinitos además de `<= 0`
- tests usan `pytest.raises`
- cobertura adicional para `math.nan` y `math.inf`
- mergeado en `526f240`

### PR-63 — Metadata estructurada para `risk_events`
**Estado:** ✅ Mergeado

**Objetivo**
Agregar contexto estructurado a `risk_events` (por ejemplo símbolo, source, códigos de error y payload operativo mínimo) para acelerar debugging y postmortems sin depender de parsear `message` libre.

**Entregables**
- columna JSON estructurada en `risk_events`
- persistencia de `context` desde `TradePlanService` sin aplanarlo solo dentro de `message`
- helpers para persistir contexto en eventos críticos de ejecución/reconcile
- command center expone metadata útil cuando exista
- migración Alembic + cobertura de tests del flujo persistencia/serialización
- mergeado en `00ad36b`

### PR-64 — Hacer visible `risk_events.context_json` en el command center
**Estado:** ✅ Mergeado

**Objetivo**
Consumir visualmente la metadata estructurada recién agregada a `risk_events` para que el debugging operativo no dependa solo del endpoint JSON o consultas SQL.

**Entregables**
- tipado front para `context` en `risk_event_history` y `recent_risk_events`
- chips/labels visuales con claves relevantes del contexto (`symbol`, `side`, `binance_side`, `quantity`, `external_order_id`, etc.)
- visualización usable en drill-down y feed global de eventos de riesgo
- validación con `next build` y deploy posterior en Synology
- mergeado en `f14db14`

### PR-65 — Resumen contextual del último riesgo por operación
**Estado:** ✅ Mergeado

**Objetivo**
Llevar el contexto del último evento de riesgo al resumen principal de cada operación para acelerar lectura operativa sin depender del historial detallado.

**Entregables**
- nuevo campo `latest_risk_context` en `operation_snapshots`
- serialización backend desde el último `RiskEvent`
- renderizado de chips/contexto también en la celda resumen de riesgo
- cobertura en tests de servicio/route + validación `next build`
- mergeado en `9b1bb33`

### PR-66 — Smoke Synology para contexto de riesgo
**Estado:** ✅ Mergeado

**Objetivo**
Hacer que el smoke Synology proteja explícitamente los marcadores de observabilidad agregados en `PR-64` y `PR-65`, tanto en payload API como en la UI del command center.

**Entregables**
- `scripts/synology_smoke_test.sh` exige `latest_risk_context` en `operation_snapshots`
- smoke valida `context` en `recent_risk_events`
- smoke exige `context-list` / `context-chip` en la home del dashboard
- `docs/plans/synology-runbook.md` actualiza el criterio mínimo de aprobación
- mergeado en `95e1c39`

### PR-67 — Cobertura testeable del smoke para contexto
**Estado:** ✅ Mergeado

**Objetivo**
Cubrir con tests reproducibles la lógica condicional introducida en `PR-66`, separando la validación del payload del smoke Synology para no depender solo del NAS real.

**Entregables**
- helper testeable `scripts/synology_smoke_context_check.py`
- tests para payload limpio/vacío y payload con contexto útil
- `scripts/synology_smoke_test.sh` invoca el helper en lugar de mantener Python embebido
- validación local + smoke real contra Synology
- mergeado en `bca67a6`

### PR-68 — Manejo limpio de errores CLI del helper de smoke
**Estado:** ✅ Mergeado

**Objetivo**
Hacer que el helper del smoke falle con mensajes claros en `stderr` y códigos de salida predecibles cuando el archivo no exista, el JSON sea inválido o el payload no cumpla el contrato esperado.

**Entregables**
- `main()` captura `FileNotFoundError`, `JSONDecodeError` y `ValueError`
- mensajes de error amigables en `stderr`
- tests del entrypoint para archivo ausente, JSON inválido y payload inválido
- validación local + smoke real contra Synology
- mergeado en `c5396d7`

### PR-69 — Fixtures locales para el shell smoke
**Estado:** ✅ Mergeado

**Objetivo**
Cubrir el contrato completo de `scripts/synology_smoke_test.sh` con un fixture local reproducible, de modo que el gating HTML condicional quede validado en CI sin depender del NAS real.

**Entregables**
- test end-to-end con servidor HTTP local para el shell smoke
- caso con contexto real + `context-list` / `context-chip` presentes
- caso limpio sin markers HTML, esperado como PASS
- caso de fallo cuando el payload exige markers pero la home no los trae
- mergeado en `11eb418`

### PR-70 — Cierre formal de Fase 14 + hardening final del fixture shell
**Estado:** ✅ Mergeado

**Objetivo**
Cerrar formalmente la Fase 14 en la documentación del repo y eliminar la fricción menor restante del fixture shell para dejar el harness operativo con teardown determinista y tipado explícito.

**Entregables**
- `run_fixture_server` con anotación explícita de retorno
- helper compartido para apagar servidor fixture + verificar cierre real del thread
- documento de cierre formal `docs/plans/phase14-observability-closure.md`
- apertura documentada de la Fase 15 en roadmap/master-plan/PR roadmap
- mergeado en `6f5a580`

### PR-71 — Cobertura shell para payload inválido del command center
**Estado:** ✅ Mergeado

**Objetivo**
Cubrir end-to-end el failure mode donde `/dashboard/command-center` devuelve un payload inválido y el shell smoke debe fallar propagando el error del helper de contexto, no pasar silenciosamente.

**Entregables**
- test shell con payload inválido (`recent_risk_events[*]` sin `context`)
- validación explícita del mensaje de error propagado por `synology_smoke_context_check.py`
- roadmap/master-plan/PR roadmap actualizados con el avance de Fase 15
- mergeado en `5204364`

### PR-72 — Cobertura shell para fallos HTTP base
**Estado:** ✅ Mergeado

**Objetivo**
Cubrir con fixture local los fallos HTTP base más importantes del smoke (`/health` no-200 y `/metrics` inesperado sin auth), garantizando que `synology_smoke_test.sh` rompa de forma clara y reproducible.

**Entregables**
- fixture HTTP con overrides por ruta
- test shell donde `/health` responde no-200
- test shell donde `/metrics` responde estado inesperado sin `METRICS_API_KEY`
- roadmap/master-plan/PR roadmap actualizados con el nuevo avance de Fase 15
- mergeado en `43c1c1c`


## Criterio de avance
No abrir el siguiente PR como “en progreso” hasta dejar el anterior con:
- checks terminados
- documentación actualizada
- comentarios/reviews resueltos
- estado consolidado en memoria
- roadmap y Gantt actualizados

---
