# ADR-023: Política de retención de artifacts operacionales

## Estado
Accepted

## Contexto
El pipeline operacional de Synology genera evidencia (`release-gate.md/json`, checklist, sign-off package y reportes auxiliares). Sin una política de retención, la carpeta `artifacts/` crece indefinidamente y dificulta auditoría efectiva.

Tras cerrar PR-19/PR-20/PR-21, el siguiente paso de Fase 6 requiere gobierno de evidencia con reglas explícitas y automatizables.

## Decisión
Se adopta una política de retención con base en días y ejecución automatizable:

1. Script oficial: `scripts/synology_artifact_retention.py`
2. Ejecución estándar por Make: `make synology-artifact-retention`
3. Reporte JSON por corrida: `artifacts-retention/synology-artifact-retention.json`
4. Modo de operación:
   - `RETENTION_DRY_RUN=true` para validación no destructiva
   - `RETENTION_DRY_RUN=false` para aplicar eliminación real
5. Workflow de GitHub Actions en modo **dry-run solamente** (sin borrado), para validación y trazabilidad.
6. Ventanas recomendadas:
   - 30 días (agresivo)
   - 45 días (balanceado, default)
   - 90 días (conservador)

## Consecuencias
### Positivas
- Evidencia operacional más fácil de auditar.
- Crecimiento de disco controlado.
- Mecanismo repetible para housekeeping.

### Riesgos
- Eliminación no intencional si `KEEP_DAYS` es demasiado bajo.
- Mitigación: usar dry-run previo y revisar JSON antes de aplicar.

## Implementación asociada
- `scripts/synology_artifact_retention.py`
- `Makefile` (`synology-artifact-retention`)
- `.github/workflows/synology-artifact-retention.yml`
- `docs/plans/synology-runbook.md`
