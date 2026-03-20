# G-Stack Decision Log

Registro corto de decisiones del piloto metodológico. Mantener entradas breves y operativas.

## Formato sugerido
- **Fecha:** YYYY-MM-DD
- **Decisión:**
- **Motivo:**
- **Impacto esperado:**
- **Follow-up:**

---

## 2026-03-20 — Adoptar piloto G-Stack en el trading bot
- **Decisión:** adoptar la metodología G-Stack como piloto de ejecución para el proyecto `binance-futures-algo-bot`.
- **Motivo:** dar más foco, ownership y evidencia al trabajo del repo sin reemplazar el flujo actual por PR ni los guardrails de riesgo ya existentes.
- **Impacto esperado:** ciclos más claros, PRs con mejor framing, mejor disciplina de sign-off y menos ambigüedad operativa.
- **Follow-up:** ejecutar una primera ventana de 2 semanas con scoreboard, one bet y roadmap de PRs acotado.

## 2026-03-20 — Mantener el flujo actual del repo como base
- **Decisión:** no reemplazar la gobernanza existente de `docs/pr-plan/PR_ROADMAP.md`; el piloto se monta encima del flujo actual.
- **Motivo:** el proyecto ya tiene trazabilidad fuerte por PR, ADR, smoke, release gate y sync documental; reescribir eso sería burocracia con esteroides.
- **Impacto esperado:** adopción incremental y de bajo riesgo.
- **Follow-up:** usar un roadmap piloto corto y enlazarlo al roadmap principal.

## 2026-03-20 — Empezar por confiabilidad operativa, no por expansión funcional
- **Decisión:** la primera apuesta del piloto será fortalecer el loop operativo en Synology antes de abrir más superficie de producto/trading.
- **Motivo:** en un bot de trading, operar con más claridad y mejor evidencia vale más que sumar otra feature brillante con olor a incidente futuro.
- **Impacto esperado:** menos ambigüedad en deploy/sign-off, mejor control del estado real y mejor base para siguientes iteraciones.
- **Follow-up:** planear 2 a 4 PRs máximos enfocados en operación, observabilidad y UX del operador.
