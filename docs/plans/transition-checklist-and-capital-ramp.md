# Checklist de transición y rampa de capital (PR-34)

> Objetivo: definir condiciones **go/no-go** y un plan de rampa de capital por etapas para transicionar desde **paper → testnet → real**, con criterios de rollback explícitos.

## Principios

1. **No hay “go-live” sin evidencia.** Cada etapa exige *gates* con métricas mínimas, evidencia persistida y revisión humana.
2. **Rampa por etapas.** Se aumenta exposición sólo si se cumplen condiciones por una ventana de tiempo (no por una corrida aislada).
3. **Rollback inmediato.** Si se supera un umbral de pérdida/drawdown o se degrada la calidad operativa, se vuelve a la etapa anterior.
4. **Reproducibilidad.** Los resultados deben ser reproducibles (mismo input → mismo output) y auditables.
5. **Seguridad operacional.** Rate limiting, auth, observabilidad y “circuit breakers” deben estar activos antes de real.

## Definiciones

- **Etapa 0 (Paper):** ejecución simulada interna, sin órdenes a exchange.
- **Etapa 1 (Testnet):** órdenes reales en Binance Futures Testnet, sin riesgo monetario.
- **Etapa 2 (Real - Micro):** capital real mínimo, tamaño unitario muy bajo.
- **Etapa 3 (Real - Small):** capital real bajo, incremento gradual.
- **Etapa 4 (Real - Target):** capital objetivo (según política de riesgo).

### Severidad de incidentes (para criterios de rollback)

- **P0:** incidente crítico. Ejemplos: bypass de guardrails de riesgo, órdenes/posiciones en estado inconsistente no reconciliable, pérdida de control de exposición, caída prolongada del sistema (sin ejecución/monitorización) o cualquier condición que requiera congelar entradas de inmediato.
- **P1:** incidente mayor. Ejemplos: degradación operativa repetida (timeouts/reintentos agotados), drift recurrente paper vs testnet sin causa explicada, latencia que impide cumplir SLA operativo, fallos intermitentes que no rompen seguridad pero sí confiabilidad.

## Gates obligatorios por etapa

### Gate A — Calidad operativa (OBLIGATORIO desde Etapa 0)

**Condiciones mínimas:**
- CI verde y reproducible.
- `synology-release-gate` OK.
- Smoke tests Synology OK.
- Backups verificables (bundle + verify-restore).
- Observabilidad operacional activa (report diario + alertas).
- Secretos en NAS (no en repo), rotación documentada.

**Evidencia requerida (artefactos):**
- Último reporte del release gate.
- Resumen JSON del gate.
- Último reporte de backup verify-restore.
- Último reporte de observabilidad.

### Gate B — Robustez cuantitativa (OBLIGATORIO para salir de Paper)

**Condiciones mínimas:**
- Backtesting/walk-forward ejecutable vía endpoint y/o servicio.
- Comparación contra benchmark (buy-and-hold u otro baseline).
- Resultados estables en múltiples periodos (definir al menos 3 rangos).
  - Definición inicial de estabilidad: evaluar **>= 3 periodos** y exigir que, en cada periodo, se cumpla el umbral mínimo de Gate B; además, que el **profit factor** y el **max drawdown** no varíen más de **±25%** respecto a la mediana entre periodos.

**Métricas mínimas sugeridas (ajustables):**
- Profit factor > **1.3** (mínimo inicial; calibrar por fees/slippage y timeframe)
- Max drawdown <= **15%**
- Trades suficientes (no “sobreajuste por 3 trades”) — mínimo inicial: **>= 200 trades por periodo** (cada uno de los periodos evaluados).

**Evidencia requerida:**
- Reporte reproducible del backtest (inputs + outputs + versión del código).
- Semilla/fixtures usadas en tests (si aplica).

### Gate C — Paridad Paper vs Testnet (OBLIGATORIO para salir de Testnet)

**Condiciones mínimas:**
- Shadow run activo: comparar decisiones paper vs ejecución testnet.
- **Duración mínima:** **>= 7 días** de shadow run **y** **>= 200 trades** acumulados en la ventana (para evitar falsos positivos por baja muestra).
- Brecha documentada y acotada.

**Métricas sugeridas (umbrales iniciales):**
- Desvío de slippage vs supuesto <= **20%**.
  - Si `slippage_modelado > 0`: |slippage_real - slippage_modelado| / slippage_modelado
  - Si `slippage_modelado = 0`: |slippage_real| <= **1 bp** (umbral absoluto)
- Desvío de fill rate <= **2%** (fills esperados vs fills efectivos en ventanas comparables).
- Errores operativos:
  - rolling **30 días**: promedio **<= 1/día**
  - rolling **7 días**: máximo **<= 3**
  (timeouts, rejects no esperados, reintentos agotados)

**Evidencia requerida:**
- Reporte de paridad por corrida.

### Gate D — Seguridad + límites de riesgo (OBLIGATORIO para Real)

**Condiciones mínimas:**
- `RiskEngine` y `FinalDecisionGate` sin bypass.
- Circuit breakers activos.
- Límites por símbolo y por portafolio activos.
- Autenticación y rate limiting en endpoints sensibles.

**Evidencia requerida:**
- Tests **y** runbook demostrando rechazo por risk limits.

## Política de rampa de capital (propuesta)

> Nota: los porcentajes se calibran contra el **presupuesto de riesgo** y el sizing del `RiskEngine`.

### Etapa 2 — Real (Micro)
- Exposición: **1× unidad mínima** o **<= 0.25%** del capital objetivo.
- Duración mínima: **7 días** **y** **>= 30 trades**.
- Criterio de rollback:
  - 2 eventos de circuit breaker en 24h, o
  - drawdown > **2%** desde el último máximo (medición intra-etapa).

### Etapa 3 — Real (Small)
- Exposición: **0.5% → 2%** del capital objetivo, por incrementos de **+0.25%** (máximo 1 incremento cada 7 días, condicionado a gates/estabilidad).
- Duración mínima: **14 días** **y** **>= 60 trades**.
- Incremento permitido: sólo si métricas y estabilidad operativa cumplen (**sin incidentes P0** y con **<= 1 incidente P1** en los últimos 7 días).
- Criterio de rollback:
  - drawdown > **5%** desde el último máximo, o
  - 1 incidente **P0**, o
  - **2 incidentes P1 en 7 días**.

### Etapa 4 — Real (Target)
- Exposición: según presupuesto de riesgo aprobado.
- Mantener guardrails de crecimiento (p. ej. +10% semanal máximo) hasta cumplir **evidencia suficiente**.
  - Definición inicial de evidencia suficiente: **>= 30 días** en Etapa 3 con métricas dentro de umbrales, **0 incidentes P0** y **<= 2 incidentes P1**, y paridad paper↔testnet estable según Gate C.
- Criterio de rollback:
  - drawdown > **10%** desde el último máximo, o
  - 2 incidentes P1 en 7 días, o
  - cualquier P0.

## Plan de rollback

1. **Congelar nuevas entradas** (permitir sólo gestión de posiciones existentes si corresponde).
2. **Reducir exposición** en un máximo de **10 minutos**:
   - Incidente **P0** → reducir a **0** (cerrar/hedgear posiciones según runbook) y congelar entradas.
   - Incidente **P1** o degradación operativa no crítica → reducir a **micro** y congelar entradas hasta completar análisis.
3. **Emitir incidente** (registro y notificación).
4. **Postmortem** con causa raíz y corrección antes de reintentar.

## Checklist Go/No-Go (resumen)

- [ ] Gate A (calidad operativa) cumplido + evidencia.
- [ ] Gate B (robustez cuantitativa) cumplido + evidencia.
- [ ] Gate C (paridad paper vs testnet) cumplido + evidencia.
- [ ] Gate D (seguridad + límites de riesgo) cumplido + evidencia.
- [ ] Runbook actualizado con pasos de transición.
- [ ] Plan de rollback probado (al menos en testnet).

## Próximos pasos

- Convertir “métricas sugeridas” en **umbrales explícitos** por estrategia.
- Definir formato de reporte reproducible (JSON + Markdown) para transición.
- Preparar PR-35: cutover controlado + monitoreo post-cutover.
