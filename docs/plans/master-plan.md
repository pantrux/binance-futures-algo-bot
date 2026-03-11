# Plan maestro de diseño e implementación (end-to-end)

## Propósito
Definir un plan cerrado de principio a fin para construir, operar y endurecer el bot de Binance Futures sin improvisación de etapas.

## Resultado final objetivo
Un sistema de trading algorítmico **auditable, resiliente y operable** en Synology, con:
- pipeline completo: datos → señales → riesgo → ejecución → observabilidad,
- operación continua con evidencias automáticas y políticas de continuidad,
- criterios formales de transición (paper → testnet → eventual live),
- documentación sincronizada y ordenada en repo + Outline.

## Arquitectura objetivo
1. **Ingesta de datos** (OHLCV, snapshots, funding/open interest).
2. **Capa técnica de señales** (indicadores + features).
3. **Capa de decisión de riesgo** (régimen, sizing, correlación, gate).
4. **Capa de ejecución** (paper + testnet + reconciliación).
5. **Capa operativa** (preflight/smoke/release gate/sign-off).
6. **Observabilidad y continuidad** (métricas, alertas, DR, retención).
7. **Gobernanza documental** (ADRs, roadmaps, sync idempotente a Outline).

## Etapas oficiales del programa

### Etapa A — Fundaciones (completada)
- PR-1 a PR-7.
- Entrega: repo gobernado por PR, ingesta robusta, señales y worker market-driven.

### Etapa B — Operación controlada (completada)
- PR-8 a PR-18.
- Entrega: observabilidad baseline, gates operativos, sign-off y cierre formal de fase.

### Etapa C — Gobernanza documental (en cierre)
- PR-19.
- Entrega: estructura documental ordenada + sync idempotente sin duplicados en Outline.

### Etapa D — Infraestructura recurrente (próxima)
- PR-20 a PR-24.
- Entrega: cron operativo, retención de artifacts, alerting, DR, hardening de seguridad.

### Etapa E — Riesgo cuantitativo avanzado
- PR-25 a PR-28.
- Entrega: régimen de mercado, sizing dinámico, correlación de portafolio, gate final avanzado.

### Etapa F — Ejecución robusta en exchange
- PR-29 a PR-31.
- Entrega: router testnet, reconciliación/state machine, paridad paper-vs-testnet.

### Etapa G — Go-live readiness
- PR-32 a PR-34.
- Entrega: backtesting/walk-forward, checklist de transición, cutover controlado.

## Reglas inmutables del plan
- `PAPER_TRADING=true` hasta completar criterios de transición de Etapa G.
- Ningún PR se cierra con comentarios/reviews abiertos.
- Cada PR debe cerrar con evidencia: checks + docs + roadmap + sync Outline.
- Cambios fuera del plan requieren ADR y actualización explícita del roadmap.
