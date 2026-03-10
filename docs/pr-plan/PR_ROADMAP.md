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

## Estado actual del proyecto
Las fases fundacionales iniciales fueron empujadas directamente a `main` para bootstrap del repo greenfield. Desde este documento en adelante, el proyecto migra formalmente a workflow por PR.

## Secuencia de PRs recomendada

### PR-1 — Gobierno del repositorio y workflow por PR
**Objetivo**
Formalizar el carril de trabajo por Pull Requests.

**Entregables**
- `docs/pr-plan/PR_ROADMAP.md`
- `docs/pr-plan/PR_TEMPLATE_CHECKLIST.md`
- `.github/pull_request_template.md`
- actualización de runbook/README si aplica

**Checks mínimos**
- CI verde
- documentación sincronizada en Outline

---

### PR-2 — Ingesta inicial de mercado Binance
**Objetivo**
Capturar OHLCV básico y snapshot de mercado para alimentar al worker con datos reales.

**Entregables**
- cliente de market data
- modelos persistentes de snapshots / candles
- endpoint/scheduler mínimo
- docs + diagramas

---

### PR-3 — Indicadores técnicos base
**Objetivo**
Implementar la primera capa de indicadores calculados sobre candles persistidos.

**Entregables**
- EMA
- RSI
- ATR
- momentum
- tests
- docs/ADR si cambia diseño

---

### PR-4 — Worker market-driven
**Objetivo**
Reemplazar el loop demo estático por generación de trade plans basada en datos de mercado reales, manteniendo fallback demo.

**Entregables**
- worker híbrido demo/market
- reglas de activación
- persistencia de señales/insights
- documentación

---

### PR-5 — Despliegue real en Synology
**Objetivo**
Llevar el stack a contenedores reales dentro del NAS.

**Entregables**
- build/deploy real
- verificación health
- validación endpoints
- validación dashboard
- runbook operativo final

**Gate extra**
No activar live trading. Solo deploy + smoke tests + paper/testnet.

---

### PR-6 — Observabilidad y hardening operativo
**Objetivo**
Agregar salud operativa, métricas y controles de incidentes.

**Entregables**
- métricas
- logs estructurados
- alertas
- eventos de riesgo ampliados
- documentación

## Criterio de avance
No abrir el siguiente PR como “en progreso” hasta dejar el anterior con:
- checks terminados
- documentación actualizada
- comentarios/reviews resueltos
- estado consolidado en memoria
