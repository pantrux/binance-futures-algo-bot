# Piloto metodológico G-Stack para Binance Futures Algo Bot

## Propósito
Adoptar como **piloto** la metodología descrita en el análisis `gstack-garrytangstack-analisis-e-integracion-con-openclaw`, aterrizándola al contexto real del bot de trading sin rehacer artificialmente el proyecto ni romper el flujo actual por PRs.

La idea no es "rebautizar" todo lo que ya existe, sino añadir una capa de operación más disciplinada:

- una apuesta principal por ciclo,
- lotes pequeños con evidencia,
- ownership claro,
- métricas visibles,
- cierre explícito de aprendizaje y siguientes decisiones.

## Hipótesis del piloto
Si operamos el proyecto con ciclos cortos, ownership explícito y una sola apuesta prioritaria por ventana, entonces deberíamos mejorar simultáneamente:

1. **claridad de ejecución**,
2. **velocidad de entrega**,
3. **calidad del sign-off**,
4. **operabilidad en Synology**,
5. **disciplina de documentación**.

## Principios adoptados

### 1. Una apuesta principal por ciclo
Cada ciclo debe responder una sola pregunta importante. Ejemplos válidos:

- ¿podemos confiar en el loop `change -> deploy -> smoke -> sign-off`?
- ¿podemos reducir falsos positivos de drift en shadow run?
- ¿podemos mejorar la workstation sin degradar el operador ni el smoke Synology?

Todo lo demás se clasifica como:
- soporte a la apuesta,
- deuda necesaria,
- o backlog explícito.

### 2. PRs pequeños y trazables
Seguimos usando el flujo formal del repo:

- `1 rama = 1 PR = 1 objetivo claro`
- evidencia obligatoria
- docs actualizadas
- sync a Outline cuando corresponda

La diferencia del piloto es que ahora cada PR debe declarar además:
- qué apuesta del ciclo soporta,
- qué métrica mueve,
- cuál es su rollback simple.

### 3. Riesgo primero
En este proyecto, una mejora bonita que debilita control de riesgo vale menos que un fix aburrido que evita pérdida o ejecución incorrecta.

Orden de prioridad operativo:
1. seguridad del capital / guardrails,
2. consistencia de ejecución,
3. operabilidad,
4. observabilidad,
5. UX del operador,
6. velocidad de expansión funcional.

### 4. Evidencia sobre narrativa
No se considera avance real si no deja evidencia verificable:

- test o smoke,
- artifact,
- runbook actualizado,
- ADR o decision log si cambia un criterio importante.

### 5. Documentación viva
Todo cambio relevante debe terminar reflejado en:
- `docs/`
- Outline
- roadmap / scoreboard del ciclo

## Alcance del piloto

### Incluye
- gobernanza semanal del trabajo
- scoreboard visible
- decisión explícita de la apuesta principal
- PR roadmap corto por ciclo
- review de métricas y riesgos al cierre

### No incluye
- reestructurar por completo el monorepo
- cambiar ADRs históricas solo por estilo
- introducir ceremonias pesadas tipo corporativo con más documento que ejecución
- abrir muchos frentes simultáneos por ansiedad de roadmap

## Estructura operativa del piloto

### Streams oficiales

#### A. Trading core
- señales
- régimen
- sizing
- execution guards

#### B. Risk-first
- `RiskEngine`
- circuit breakers
- límites agregados
- drift y reconcile

#### C. Operación Synology
- preflight
- smoke
- release gate
- backup/restore
- sign-off

#### D. Observabilidad
- métricas
- risk events
- reporting diario
- freshness y cobertura live

#### E. Operator UX
- workstation
- command center
- drill-down
- herramientas seguras de diagnóstico

#### F. Documentación y decisión
- ADRs
- roadmap
- scoreboards
- runbooks
- sync Outline

## Cadencia del piloto

### Inicio de ciclo
Definir:
- apuesta principal,
- objetivo observable,
- 2 a 4 PRs máximos,
- riesgos principales,
- criterio de éxito,
- criterio de rollback.

### Durante el ciclo
Cada PR debe indicar:
- objetivo concreto,
- impacto esperado,
- checks,
- evidencia,
- riesgo residual.

### Cierre de ciclo
Revisar:
- qué se completó,
- qué no movió la métrica esperada,
- qué quedó como deuda explícita,
- qué decisión cambia para el siguiente ciclo.

## Métricas del piloto

### Métricas principales
- lead time por PR
- tasa de checks verdes al primer intento
- cantidad de fallos detectados por smoke/release gate
- cantidad de incidentes o drift operativo detectados post-merge
- tiempo desde cambio hasta evidencia de deploy verificable

### Métricas secundarias
- porcentaje de PRs con docs actualizadas
- porcentaje de PRs con rollback explícito
- número de follow-ups abiertos por deuda residual de review
- cantidad de decisiones relevantes sin ADR/decision log

## Apuesta inicial recomendada
La apuesta inicial del piloto será:

> **hacer más confiable el loop operativo completo del bot en Synology sin degradar riesgo ni visibilidad del operador**.

Eso significa priorizar:
- release gate,
- observabilidad útil,
- workstation operable,
- documentación y sign-off claros.

## Entregables del piloto
Este piloto se formaliza con los siguientes documentos activos:

- `docs/plans/gstack-pilot.md`
- `docs/plans/gstack-scoreboard.md`
- `docs/plans/gstack-decision-log.md`
- `docs/pr-plan/GSTACK_PR_PILOT_ROADMAP.md`

## Criterio de éxito del piloto
Consideraremos el piloto exitoso si al cierre de la primera ventana logramos:

1. ejecutar un ciclo completo con apuesta explícita,
2. cerrar PRs pequeños con evidencia y rollback claro,
3. mantener `RiskEngine` y gates operativos intactos,
4. dejar scoreboard y decision log actualizados,
5. demostrar que el método reduce ambigüedad y no añade burocracia inútil.

## Criterio de cancelación
Se cancela o reajusta el piloto si ocurre cualquiera de estas condiciones:

- aumenta la fricción documental sin mejorar claridad,
- se abren demasiados frentes paralelos,
- el método compite con los guardrails del bot,
- el equipo termina produciendo más ritual que evidencia.
