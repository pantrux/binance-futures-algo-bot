# ADR-025 — Resiliencia operacional: backup/recovery y hardening base

- **Estado:** Aprobada
- **Fecha:** 2026-03-12
- **PR:** PR-24

## Contexto

Tras completar PR-22 (retención de artifacts) y PR-23 (observabilidad/alerting), faltaba cubrir la continuidad operacional ante incidentes:

1. evidencia reproducible de backup/restore de configuración crítica,
2. criterio mínimo de RTO/RPO documentado,
3. verificación periódica automática de capacidad de recuperación.

## Decisión

Se implementa una capa base de resiliencia para configuración crítica Synology:

- Script `scripts/synology_resilience_backup.py`:
  - empaqueta archivos críticos en bundle tar.gz,
  - genera manifest JSON con hashes SHA-256,
  - permite verificación de restore en entorno temporal (`--verify-restore`),
  - registra objetivos RTO/RPO en la evidencia.

- Target Make `synology-resilience-backup`:
  - ejecución operativa estandarizada desde CLI.

- Workflow `Synology Resilience Backup Verify`:
  - schedule diario + dispatch manual,
  - genera y publica evidencia (`manifest + bundle`) como artifact CI.

## RTO/RPO iniciales

- **RTO objetivo inicial:** 60 minutos.
- **RPO objetivo inicial:** 1440 minutos (24 horas).

Estos objetivos son baseline operativo y deberán refinarse cuando la fase de DR completo se expanda.

## Consecuencias

### Positivas
- Se reduce riesgo de pérdida operativa por falta de procedimiento de recuperación.
- El restore deja evidencia auditable periódica en CI.
- Se habilita evolución progresiva hacia un playbook DR más completo.

### Trade-offs
- El backup actual cubre configuración crítica del repo, no datos runtime del NAS.
- El restore se valida en entorno temporal de CI; la prueba completa en NAS real sigue siendo una tarea operativa complementaria.

## Guardrails

- No habilita live trading.
- No modifica lógica core de señales/riesgo/ejecución.
- Mantener `PAPER_TRADING=true` hasta cumplir fases de transición definidas.
