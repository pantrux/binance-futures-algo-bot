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

### Etapa C — Gobernanza documental (completada)
- PR-19 y PR-20.
- Entrega: estructura documental ordenada + sync idempotente sin duplicados en Outline + estabilización de operación one-shot del worker en Synology.

### Etapa D — Infraestructura recurrente (en progreso)
- PR-22 a PR-24 (con PR-21 como ajuste documental de alineación).
- Estado actual: PR-22 ✅ mergeado (retención de artifacts), PR-23 ✅ mergeado (observabilidad/alerting), PR-24 🟡 en progreso.
- Entrega: gobierno de artifacts, cron operativo, alerting, DR y hardening de seguridad.

### Etapa E — Riesgo cuantitativo avanzado
- PR-25 a PR-28.
- Entrega: régimen de mercado, sizing dinámico, correlación de portafolio, gate final avanzado.

### Etapa F — Ejecución robusta en exchange
- PR-29 a PR-32.
- Entrega: router testnet, reconciliación/state machine, paridad paper-vs-testnet y visibilidad operativa diaria.

### Etapa G — Go-live readiness
- PR-33 a PR-35.
- Estado actual: completada con backtesting/walk-forward, checklist de transición, rampa de capital y runbook de cutover.
- Entrega: backtesting/walk-forward, checklist de transición, cutover controlado.

### Etapa H — Ensayos operativos de cutover
- PR-36 a PR-39.
- Estado actual: PR-36 y PR-37 mergeados; PR-39 en progreso.
- Entrega: drills sintéticos, paquete de evidencia, templates operativos, criterio formal de aprobación pre-live y links navegables desde Outline hacia la documentación fuente.

## Reglas inmutables del plan
- `PAPER_TRADING=true` hasta completar criterios de transición de Etapa G y aprobar ensayos operativos de Etapa H.
- Ningún PR se cierra con comentarios/reviews abiertos.
- Cada PR debe cerrar con evidencia: checks + docs + roadmap + sync Outline.
- Cambios fuera del plan requieren ADR y actualización explícita del roadmap.
