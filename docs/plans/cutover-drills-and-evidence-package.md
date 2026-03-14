# Drills sintéticos y paquete de evidencia de cutover (PR-36)

> Objetivo: convertir el runbook de cutover en una práctica **ensayable, auditable y repetible** antes de cualquier transición real de exposición. Este documento complementa `cutover-and-post-cutover-monitoring.md` con ejercicios controlados y un paquete estándar de evidencia.

## Alcance

- catálogo mínimo de drills previos a cutover
- evidencia obligatoria por drill y por cutover
- plantillas mínimas para reporte inicial, incidente y cierre
- criterio de aprobación / rechazo del ensayo

## Regla operativa

**No se ejecuta un cutover real** si antes no existe al menos **1 corrida documentada** de drills sintéticos **aprobada según el criterio formal de este documento** y con evidencia archivada.

## Catálogo mínimo de drills

### Drill 1 — Alertas críticas

**Objetivo:** validar que los canales y reglas críticas realmente notifican.

**Pruebas mínimas:**
- alerta de caída total del sistema
- alerta de drift paper vs testnet
- alerta de rejects / errores operativos
- alerta de latencia degradada

**Evidencia requerida:**
- timestamp del disparo
- canal receptor
- tiempo hasta recepción
- payload resumido
- resultado (`OK` / `WARN` / `FAIL`)

### Drill 2 — Reporte diario y snapshot operativo

**Objetivo:** confirmar que el sistema emite el reporte operativo sin intervención manual.

**Pruebas mínimas:**
- generar resumen diario en Markdown
- generar resumen estructurado en JSON
- verificar presencia de métricas clave (latencia, rejects, slippage, reconciliación)

**Evidencia requerida:**
- artifact Markdown
- artifact JSON
- checksum / timestamp
- validación humana breve
- resultado (`OK` / `WARN` / `FAIL`)

### Drill 3 — Rollback dry-run

**Objetivo:** verificar que el rollback puede ejecutarse en tiempo objetivo sin improvisación.

**Pruebas mínimas:**
- congelar nuevas entradas
- reducir exposición a `micro` o `0` según severidad simulada
- emitir incidente y snapshot de evidencia
- dejar checklist de reintento bloqueada durante 24 h

**Objetivo de tiempo:** <= **10 min** para transición a estado seguro.

**Evidencia requerida:**
- cronología minuto a minuto
- comandos/acciones ejecutadas
- tiempo total hasta estado seguro
- resultado (`OK` / `WARN` / `FAIL`)

### Drill 4 — Reconciliación y consistencia

**Objetivo:** confirmar que el operador detecta y clasifica desvíos entre órdenes, posiciones y reportes.

**Pruebas mínimas:**
- revisar reconciliación de posiciones
- revisar diferencias paper/testnet si shadow run sigue activo
- clasificar un incidente ficticio como `P0` o `P1`

**Evidencia requerida:**
- resumen de diferencias observadas
- clasificación elegida y justificación
- decisión operativa resultante
- resultado (`OK` / `WARN` / `FAIL`)

## Paquete de evidencia obligatorio

Cada cutover o ensayo debe dejar un paquete mínimo con:

1. **`cutover-initial-report.md`**
   - template base: `docs/templates/cutover-initial-report-template.md`
   - contexto
   - versión / commit
   - entorno objetivo
   - hora de inicio
   - checkpoints esperados

2. **`cutover-initial-report.json`**
   - template base: `docs/templates/cutover-initial-report-template.json`
   - mismos campos en formato máquina-legible

3. **`incident-log.md`**
   - template base: `docs/templates/incident-log-template.md`
   - timestamp
   - incidente
   - severidad
   - impacto
   - mitigación
   - owner

4. **`drill-results.md`**
   - template base: `docs/templates/drill-results-template.md`
   - tabla de drills ejecutados
   - resultado
   - evidencia enlazada
   - observaciones

5. **`post-cutover-closeout.md`**
   - template base: `docs/templates/post-cutover-closeout-template.md`
   - cierre inicial 24 h
   - cierre formal 7 días
   - decisión final: continuar / mantener micro / rollback

## Plantilla mínima de tabla para `drill-results.md`

| Drill | Fecha | Resultado | Evidencia | Observaciones |
|---|---|---|---|---|
| Alertas críticas | YYYY-MM-DD HH:MM UTC | OK/WARN/FAIL | link o artifact | nota breve |
| Reporte diario | YYYY-MM-DD HH:MM UTC | OK/WARN/FAIL | link o artifact | nota breve |
| Rollback dry-run | YYYY-MM-DD HH:MM UTC | OK/WARN/FAIL | link o artifact | nota breve |
| Reconciliación | YYYY-MM-DD HH:MM UTC | OK/WARN/FAIL | link o artifact | nota breve |

## Criterio de aprobación del ensayo

Para esta fase, **todos los drills del catálogo se consideran críticos** hasta acumular historia operativa real.

Un ensayo queda **aprobado** solo si:

- no hay `FAIL` en ningún drill crítico,
- los tiempos objetivo se cumplen,
- existe evidencia Markdown + JSON,
- y cualquier `WARN` tiene mitigación explícita y fecha de seguimiento.

## Criterio para habilitar cutover real

- `PR-34` cumplido con evidencia
- `PR-35` vigente y aceptado como runbook operativo
- drills sintéticos aprobados
- paquete de evidencia archivado y enlazable en Outline
- revisión humana final registrada
