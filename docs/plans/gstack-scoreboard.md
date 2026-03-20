# G-Stack Scoreboard — piloto inicial

## Estado del piloto
- **Estado:** Activo
- **Ventana inicial sugerida:** 2 semanas
- **Modo:** piloto operativo, no cambio total de metodología
- **Apuesta principal:** confiabilidad del loop operativo en Synology

## One Bet
> Mejorar el ciclo `cambio -> validación -> deploy -> evidencia -> sign-off` para que el bot avance con más claridad y menos ambigüedad operativa.

## Objetivo observable
Reducir fricción y aumentar confianza al entregar cambios del trading bot, priorizando evidencia verificable sobre progreso percibido.

## Métricas objetivo

| Métrica | Baseline | Objetivo piloto | Notas |
|---|---:|---:|---|
| Lead time por PR | TBD | bajar o mantener sin degradar calidad | medir desde apertura a merge |
| Checks verdes al primer intento | TBD | >= 80% | incluye build/test/lint/smoke relevantes |
| PRs con rollback explícito | 0%/no formalizado | 100% | aunque sea rollback simple |
| PRs con docs actualizadas | alto pero variable | 100% | docs + roadmap + Outline cuando aplique |
| Fallos detectados por gates antes de merge/deploy | TBD | subir detección temprana | aquí "más" puede ser saludable |
| Incidentes post-merge atribuibles a falta de evidencia | TBD | tender a 0 | especialmente en Synology/testnet |

## Riesgos top del ciclo
1. Abrir demasiados frentes a la vez y diluir la apuesta principal.
2. Seguir mejorando UX sin reforzar el loop operativo completo.
3. Crear ritual documental sin impacto real en velocidad o calidad.
4. Romper smoke/gates por cambios de workstation o payloads del command center.

## Streams del ciclo

| Stream | Prioridad | Resultado esperado |
|---|---|---|
| Operación Synology | Alta | release gate y sign-off más confiables |
| Observabilidad | Alta | señales accionables, no solo métricas decorativas |
| Workstation operador | Media-Alta | visibilidad y diagnóstico seguro sin ambigüedad |
| Risk-first | Alta | ningún cambio debe degradar guardrails |
| Documentación/Outline | Alta | evidencia y navegación clara |

## PRs sugeridos para esta ventana
1. Hardening del loop operativo / release evidence.
2. Refinamiento de métricas o artefactos para sign-off.
3. Mejora puntual de workstation que reduzca ambigüedad real del operador.
4. Sync documental final del ciclo.

## Señales de éxito
- cada PR declara objetivo, métrica y rollback;
- el roadmap del ciclo cabe en una pantalla sin convertirse en novela rusa;
- el operador entiende el estado del bot sin abrir diez paneles ni leer té en logs;
- la evidencia de deploy/sign-off es más clara que antes.

## Señales de fracaso
- backlog creciendo más rápido que la capacidad de cierre;
- varios PRs en paralelo sin una apuesta dominante;
- updates documentales que no ayudan a decidir;
- follow-ups de review repetitivos que debieron quedar resueltos en el PR original.

## Revisión al cierre del piloto
Completar al terminar la primera ventana:

- **Resultado de la apuesta:** TBD
- **Métrica principal movida:** TBD
- **Qué funcionó:** TBD
- **Qué no funcionó:** TBD
- **Qué se mantiene del método:** TBD
- **Qué se simplifica o descarta:** TBD
