# ADR-031 — Reconciliación y máquina de estados de ejecución

## Estado
Aceptado

## Contexto
Con PR-29 existe ejecución testnet real, pero faltaba un mecanismo explícito para verificar consistencia entre el estado del `TradePlan` y los registros de `Order`/`Position`.

## Decisión
Agregar `ExecutionStateMachineService` con reconciliación por trade plan:

- valida presencia de órdenes fill cuando el plan está ejecutado,
- valida presencia de posición abierta asociada,
- detecta condiciones de drift (múltiples posiciones abiertas, órdenes rechazadas con plan ejecutado),
- diferencia entre error crítico por ausencia total de posición y warning por posición ya cerrada con plan aún ejecutado,
- emite `ReconciliationReport` con `drift_events` tipados y `recommended_actions`.

## API
- `GET /execution/reconcile/{trade_plan_id}`
  - retorna `ReconciliationReport`.

## Consecuencias
### Positivas
- permite auditoría rápida de consistencia por trade plan,
- habilita automatización futura de remediación (rebuild/replay).

### Negativas
- agrega ruta y lógica de mantenimiento adicional en API.

### Neutrales
- no modifica el flujo de ejecución actual; solo añade observabilidad/reconciliación.
