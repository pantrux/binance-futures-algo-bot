# ADR-040 — Gate auditable de shadow run para readiness testnet

## Estado
Aceptado

## Contexto
Con `PR-31` ya existe comparación paper vs testnet por símbolo y con `PR-32` ya existen alertas/resúmenes operativos. Sin embargo, faltaba una pieza crítica para decidir si el bot puede entrar a una etapa de **testnet serio** o avanzar luego hacia **real-micro** sin depender de inspección manual dispersa.

La checklist de transición (`PR-34`) exige evidencia explícita para Gate C:
- duración mínima de shadow run,
- volumen mínimo de trades,
- brecha paper vs testnet,
- fill rate,
- incidentes operativos dentro de umbrales.

Hasta ahora esa evidencia existía fragmentada en endpoints y tablas, pero no como un **reporte unificado, automatizable y exportable**.

## Decisión
Agregar una capa auditable de readiness de shadow run compuesta por:

1. `ShadowRunReportingService`
   - consolida en una sola salida:
     - duración observada de shadow run,
     - volumen paper/testnet,
     - pares comparados + unmatched,
     - fill rate testnet,
     - slippage promedio en bps,
     - incidentes warning/critical (7d) y promedio 30d,
     - desglose por símbolo.
2. Endpoint protegido:
   - `GET /reporting/shadow-run-summary?window_days=...`
3. Script operativo:
   - `scripts/synology_shadow_run_gate.py`
   - consume el endpoint de shadow run, evalúa umbrales y genera artefactos JSON + Markdown.
   - adicionalmente consulta `/dashboard/command-center` para adjuntar evidencia operativa reciente del command center dentro del mismo artifact.
4. Workflow GitHub Actions:
   - `.github/workflows/synology-shadow-run-gate.yml`
   - permite ejecutar/manualizar el Gate C y subir evidencia auditable como artifact.

## Consecuencias
### Positivas
- El readiness hacia testnet serio queda medible y repetible.
- La decisión de avanzar o no deja de depender de lectura manual dispersa.
- Se genera evidencia reutilizable para runbooks, auditoría y cutover.
- El artifact deja de ser solo cuantitativo y pasa a incluir contexto operacional del command center para inspección rápida de las operaciones recientes.
- Los umbrales quedan parametrizables sin reescribir la API.

### Negativas
- El gate inicial depende de la calidad de los datos persistidos (`TradePlan`, `Order`, `RiskEvent`).
- Algunas métricas siguen siendo aproximaciones operativas (por ejemplo slippage observado vs precio de entrada planificado) hasta tener una capa más rica de expected fills / modeled slippage.

### Neutrales
- No cambia la ejecución del bot; agrega una capa de evaluación y evidencia.
- Mantiene `PAPER_TRADING=true` como guardrail hasta que los gates documenten readiness suficiente.
