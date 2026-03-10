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
- [ ] Diagramas/ADR añadidos si aplica

## Operación
- [ ] Compatible con Synology-first
- [ ] Sin runtime en OpenClaw
- [ ] Variables de entorno documentadas

## Merge
- [ ] Reviews/comments revisados
- [ ] Sugerencias aplicables incorporadas o justificadas
- [ ] Listo para merge
