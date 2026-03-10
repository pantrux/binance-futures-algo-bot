# ADR-005 — Persistencia auditable de planes operativos

## Estado
Aceptado

## Decisión
Persistir cada plan operativo en PostgreSQL antes de cualquier ejecución real o simulada.

## Justificación
- Auditoría reproducible.
- Integración limpia con Outline.
- Base para métricas, backtesting operacional y journal.

## Consecuencias
- Se crea la entidad `trade_plans` como primer agregado persistente.
- Todo plan aprobado o bloqueado debe registrarse con score, régimen, riesgo aplicado y tesis.
- El deploy en Synology debe incluir PostgreSQL y migraciones.
