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
| PR-12 | Resumen JSON y evidencia máquina-legible del gate | 🟡 En progreso | parser y artifacts JSON para auditoría automatizable |

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
**Estado:** 🟡 En progreso

**Objetivo**
Transformar la salida del release gate en evidencia estructurada (JSON) para auditoría automática y trazabilidad en CI.

**Entregables**
- parser `scripts/synology_release_gate_summary.py`
- workflow `synology-release-gate.yml` con artifact JSON + job summary
- docs/runbook actualizados

**Gate extra**
Mantener `PAPER_TRADING=true` y no habilitar live trading.

## Criterio de avance
No abrir el siguiente PR como “en progreso” hasta dejar el anterior con:
- checks terminados
- documentación actualizada
- comentarios/reviews resueltos
- estado consolidado en memoria
- roadmap y Gantt actualizados
