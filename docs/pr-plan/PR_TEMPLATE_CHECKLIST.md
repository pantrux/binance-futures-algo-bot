# Checklist estándar para PRs del proyecto

## Alcance
- [ ] El objetivo del PR está acotado y claro
- [ ] No mezcla múltiples iniciativas sin relación

## Calidad técnica
- [ ] Tests locales ejecutados
- [ ] Build local ejecutado
- [ ] CI en verde

## Riesgo
- [ ] No rompe la regla global de riesgo del 5%
- [ ] No bypassea el `RiskEngine`
- [ ] Si toca ejecución, sigue siendo paper/testnet salvo instrucción explícita

## Documentación
- [ ] `docs/` actualizado
- [ ] Outline actualizado si hubo cambio de diseño o implementación
- [ ] Si se escribió en Outline, quedó evidencia del sync manual (workflow o ejecución local)
- [ ] Diagramas/ADR añadidos si aplica

## Operación
- [ ] Compatible con Synology-first
- [ ] Sin runtime en OpenClaw
- [ ] Variables de entorno documentadas
- [ ] Si hubo despliegue/cambio operacional en NAS, quedó evidencia de deploy (commit, `docker compose ps`, `docker compose images`, estado de jobs one-shot)

## Merge
- [ ] Reviews/comments revisados
- [ ] Sugerencias aplicables incorporadas o justificadas
- [ ] Listo para merge
