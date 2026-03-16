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

### Etapa D — Infraestructura recurrente (completada)
- PR-22 a PR-24 (con PR-21 como ajuste documental de alineación).
- Estado actual: PR-22 ✅, PR-23 ✅ y PR-24 ✅ mergeados.
- Entrega: gobierno de artifacts, cron operativo, alerting, DR y hardening de seguridad.

### Etapa E — Riesgo cuantitativo avanzado (completada)
- PR-25 a PR-28.
- Entrega: régimen de mercado, sizing dinámico, correlación de portafolio y gate final avanzado.

### Etapa F — Ejecución robusta en exchange (completada)
- PR-29 a PR-32.
- Entrega: router testnet, reconciliación/state machine, paridad paper-vs-testnet y visibilidad operativa diaria.

### Etapa G — Go-live readiness
- PR-33 a PR-35.
- Estado actual: completada con backtesting/walk-forward, checklist de transición, rampa de capital y runbook de cutover.
- Entrega: backtesting/walk-forward, checklist de transición, cutover controlado.

### Etapa H — Ensayos operativos de cutover
- PR-36 a PR-39.
- Estado actual: completada; PR-39 mergeado con links navegables hacia Outline/GitHub y sync validado (`docs_synced=59`).
- Entrega: drills sintéticos, paquete de evidencia, templates operativos, criterio formal de aprobación pre-live y links navegables desde Outline hacia la documentación fuente.

### Etapa I — Guardrails documentales + readiness automation
- PR-40 a PR-41.
- Estado actual: completada.
- Entrega: validación CI de links Markdown locales + gate auditable de shadow run para readiness testnet con artifacts JSON/Markdown.

### Etapa J — Activación operativa de testnet (completada)
- PR-42 a PR-52.
- Estado actual: completada; `PR-49` quedó cerrado sin merge por branch fallido/superado, y `PR-50`/`PR-51`/`PR-52` consolidaron el command center + persistencia de fill real + hardening del refresh testnet.
- Entrega: primeras ejecuciones testnet reales + normalización de fills + reconciliación robusta + centro de mando con radar/timeline/drill-down/justificación técnica + persistencia de fill real desde Binance + hardening fino del refresh post-submit.

### Etapa K — Profundización del command center
- PR-53 a PR-62.
- Estado actual: completada; el carril del command center/testnet quedó cerrado con historial operativo completo, smoke Synology específico, evidencia operacional del gate, fills reales, bloqueo de setups demo, auto-ingesta de mercado y hardening final del serializer de quantity.
- Entrega esperada: historial operativo completo por `trade_plan_id`, navegación de detalle más profunda, smoke Synology específico del command center y trazabilidad end-to-end por operación.

### Etapa L — Observabilidad operativa post-corrección
- PR-63 a PR-69.
- Estado actual: completada; el carril dejó `risk_events.context_json` operativo y visible, `latest_risk_context` disponible en resumen, smoke Synology endurecido y cobertura local end-to-end del shell smoke sin dependencia del NAS real.
- Entrega lograda: errores/eventos críticos con contexto JSON útil, visible y consultable sin parsear solo texto libre.

### Etapa M — Hardening del harness operacional
- PR-70 en adelante.
- Estado actual: completada; `PR-70` a `PR-79` dejaron el harness shell con teardown determinista, helpers más claros y cobertura reproducible de payload inválido, fallos HTTP base, auth opcional, strictness configurable de dependencias externas y ausencia de marcadores críticos de `WEB /`; `PR-80` formalizó ese cierre y `PR-81` dejó el roadmap ejecutivo consistente.
- Entrega lograda: harness operacional limpio, tipado y predecible, suficientemente endurecido para que el siguiente frente vuelva a lógica de producto/trading y no a fricción de tests.

### Etapa N — Refinamiento de paridad paper vs testnet
- PR-82 en adelante.
- Estado actual: en progreso; `PR-82` endureció el emparejamiento del shadow run para no cruzar trade plans de distinta `timeframe` dentro del mismo símbolo/lado, `PR-83` alineó con esa misma regla el `ExecutionParityService`, `PR-84/85` limpiaron el carril documental, `PR-86` añadió filtro opcional por `timeframe` al reporte puntual de parity y `PR-87` apunta a exponer el mismo filtro en el resumen agregado de shadow run.
- Entrega esperada: métricas de paridad/shadow run más confiables y consistentes entre reportes agregados y puntuales cuando existan múltiples temporalidades o estrategias concurrentes por símbolo, con filtros explícitos para consumo operativo.

## Reglas inmutables del plan
- `PAPER_TRADING=true` hasta completar criterios de transición de Etapa G y aprobar ensayos operativos de Etapa H.
- Ningún PR se cierra con comentarios/reviews abiertos.
- Cada PR debe cerrar con evidencia: checks + docs + roadmap + sync Outline.
- Cambios fuera del plan requieren ADR y actualización explícita del roadmap.
