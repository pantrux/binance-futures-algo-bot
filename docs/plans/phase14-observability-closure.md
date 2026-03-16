# Cierre operativo — Fase 14 (Observabilidad operativa post-corrección)

## Objetivo
Formalizar el cierre de la fase de observabilidad post-corrección iniciada tras los fixes críticos de testnet/command center, consolidando que el sistema ya cuenta con:
- metadata estructurada en `risk_events`
- visualización de contexto de riesgo en UI/resumen
- smoke Synology endurecido
- helper CLI del smoke testeable y con errores legibles
- cobertura local end-to-end del shell smoke sin depender del NAS real

## Criterios de cierre (obligatorios)
- [x] `risk_events.context_json` persistido en base de datos y expuesto por API
- [x] contexto de riesgo visible en el command center (`context-list` / `context-chip`)
- [x] `latest_risk_context` visible en el resumen principal por operación
- [x] smoke Synology endurecido para validar contexto de riesgo en API/UI
- [x] cobertura reproducible del helper de contexto (`payload limpio` vs `payload con contexto`)
- [x] manejo CLI limpio de errores (`FileNotFoundError`, `JSONDecodeError`, `ValueError`)
- [x] cobertura end-to-end del shell smoke con fixture HTTP local
- [x] validación real en Synology + sync Outline posterior a cada PR relevante

## PRs que cerraron la fase
- `PR-63` — metadata estructurada para `risk_events`
- `PR-64` — visibilidad de `risk_events.context_json` en UI
- `PR-65` — `latest_risk_context` en resumen por operación
- `PR-66` — smoke Synology para contexto de riesgo
- `PR-67` — cobertura testeable del helper de contexto
- `PR-68` — errores CLI limpios en helper del smoke
- `PR-69` — fixture local end-to-end para `synology_smoke_test.sh`

## Evidencia consolidada
- Validación NAS real: `GET /dashboard/command-center` con `context`/`latest_risk_context` y HTML con `context-list` / `context-chip`
- Suite local reproducible del carril smoke: helper + shell fixture + docs links
- Outline sincronizado tras el cierre de cada PR del carril

## Resultado del cierre
La fase deja al command center y al smoke operativo en un estado auditable y reproducible:
- el operador ve el contexto de riesgo útil sin parsear texto libre
- el smoke protege tanto el payload como el render UI
- CI ya puede detectar regresiones del contrato del smoke sin esperar al NAS real

## Recomendaciones post-cierre
1. Consolidar la robustez del harness operacional (fixtures, teardown determinista, ergonomía de fallos en CI).
2. Evaluar cierre formal de Fase 15 una vez que el harness quede completamente libre de flakes y con tipado/cleanup homogéneo.
3. Mantener el watcher GitHub activo solo como mecanismo de reacción; no usarlo como sustituto de cobertura reproducible en tests.
