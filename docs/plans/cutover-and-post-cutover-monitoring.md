# Cutover controlado y monitoreo post-cutover (PR-35)

> Objetivo: ejecutar un **cutover controlado** hacia testnet/real de forma segura, con runbook, validaciones, guardrails y monitoreo reforzado. Este documento asume que la checklist de transición (PR-34) se cumple y que existe evidencia almacenada.

## Alcance

- Procedimiento de cutover (pre-flight → ejecución → validación → observación)
- Playbook de incidentes y rollback
- Monitoreo post-cutover (métricas, alertas, reportes)
- Triage de degradaciones P1/P0

## Pre-flight (antes de tocar modo de ejecución)

### 1) Estado del repo y release gates

- [ ] CI verde en `main`
- [ ] `synology-release-gate` OK (última corrida)
- [ ] Backup verify-restore OK
- [ ] Secrets en NAS (no en repo), rotación documentada

### 2) Observabilidad

- [ ] Reporte diario operativo funcionando
- [ ] Alertas principales activas (caída total, drift, rejects, latencia)
- [ ] Dashboard/endpoint de health accesible y autenticado

### 3) Riesgo y seguridad

- [ ] Guardrails de riesgo habilitados (sin bypass)
- [ ] Circuit breakers habilitados
- [ ] Rate limiting y auth en endpoints sensibles

## Cutover: secuencia recomendada

### Paso 0 — Congelar cambios

- [ ] Freeze window de deploy (no merges durante la ventana)
- [ ] Tag/release pre-cutover (para rollback de código rápido)

### Paso 1 — Habilitar modo objetivo (paper → testnet / testnet → real)

- [ ] Cambiar el modo por config feature-flag (no hardcode)
- [ ] Reiniciar servicio de forma controlada
- [ ] Validar “no trades” si corresponde (modo dry-run), luego habilitar trades

### Paso 2 — Validación inmediata (primeros 15 minutos)

- [ ] Latencia y estado del exchange OK
- [ ] No hay rejects sistemáticos
- [ ] No hay drift paper vs ejecución (si shadow run sigue activo)
- [ ] No hay errores de reconciliación de posiciones

### Paso 3 — Ventana de observación

- [ ] Mantener exposición controlada según etapa (micro/small)
- [ ] Confirmar que report diario y alertas se disparan en condiciones simuladas
- [ ] Registrar incidente si hay degradación

## Post-cutover: monitoreo y gates

### Métricas mínimas a vigilar (operativas)

- Error rate (timeouts/retries exhausted/rejects)
- Latencia (p95/p99) de calls críticos a exchange
- Drift paper vs ejecución (si aplica)
- Estado de posiciones (reconciliación)
- Slippage real vs supuesto

### Métricas mínimas a vigilar (estrategia)

- Drawdown desde high-watermark
- Exposición por símbolo y total
- Número de trades (para evitar conclusiones por baja muestra)

## Rollback (runbook resumido)

1. **Congelar nuevas entradas**
2. Reducir exposición (P0→0 / P1→micro) en <= 10 minutos
3. Emitir incidente + snapshot de evidencia (logs, métricas, reporte)
4. Volver a etapa previa (paper/testnet) y revalidar gates

## Checklist de salida de ventana

- [ ] No incidentes P0
- [ ] Incidentes P1 dentro de umbrales
- [ ] Reporte post-cutover emitido (Markdown + JSON)
- [ ] Próximo checkpoint calendarizado (24h / 7d)
