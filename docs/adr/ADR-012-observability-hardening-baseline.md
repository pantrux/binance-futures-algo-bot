# ADR-012 — Observabilidad y hardening operativo (baseline)

## Estado
Aceptado (PR-8)

## Contexto
Con `PR-7` el worker ya genera planes market-driven, pero faltaba una base mínima de observabilidad para operar y diagnosticar incidentes sin depender de inspección manual del código.

Necesidades inmediatas:
- Métricas básicas del API para detectar degradación.
- Logs estructurados en API/worker para correlación rápida.
- Política explícita ante fallos parciales por símbolo.

## Decisión
Implementar una capa baseline de observabilidad con tres componentes:

1. **Métricas runtime del API**
   - Middleware HTTP que registra por request:
     - método y path
     - status code
     - latencia
   - Endpoint `GET /metrics` con snapshot agregado (protegible por `x-metrics-key` cuando `metrics_api_key` está configurada):
     - `total_requests`, `total_errors`, `error_rate_pct`
     - `latency_ms_avg`, `latency_ms_max`
     - distribución por `status_codes` y `routes`

2. **Logs estructurados JSON**
   - API: evento `api_request` con `request_id`, ruta, status y duración.
   - Worker: eventos estructurados para creación de plan, ejecución paper, fallos por símbolo y resumen de ejecución.

3. **Hardening de fallos parciales**
   - Nuevo setting `strict_symbol_failures` en `WorkerSettings` (expuesto como `STRICT_SYMBOL_FAILURES` en `.env`).
   - Política por defecto:
     - si fallan todos los símbolos, el worker termina con error.
     - si hay fallos parciales, se registran explícitamente; el fail-fast parcial es configurable con `strict_symbol_failures=True`.

## Consecuencias
### Positivas
- Diagnóstico más rápido ante incidentes operativos.
- Señales observables mínimas para futura integración con alertas externas.
- Menor ambigüedad en comportamiento del worker frente a fallos parciales.

### Trade-offs
- Métricas in-memory (se pierden al reinicio).
- No se implementa aún exportador Prometheus ni sink centralizado de logs.

## Próximos pasos sugeridos
1. Exponer métricas en formato Prometheus.
2. Definir alertas operativas (errores 5xx, latencia p95, ratio de fallback demo).
3. Persistir eventos de riesgo/ejecución para auditoría histórica.
