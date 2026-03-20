# Roadmap de PRs — piloto G-Stack

## Objetivo del piloto
Ejecutar una primera ventana corta bajo la metodología G-Stack, usando una sola apuesta principal:

> **hacer más confiable y legible el loop operativo del bot en Synology sin degradar riesgo ni velocidad de entrega**.

## Reglas del piloto
1. Máximo **2 a 4 PRs** dentro de la ventana inicial.
2. Cada PR debe declarar:
   - qué parte de la apuesta soporta,
   - qué métrica intenta mover,
   - cuál es su rollback.
3. Ningún PR del piloto puede debilitar:
   - `RiskEngine`,
   - smoke Synology,
   - release gate,
   - trazabilidad documental.
4. Si aparece un frente grande, se corta en slices más pequeños o se mueve al backlog.

## Ventana 1 — PRs sugeridos

### PR-P1 — Hardening de evidencia operativa del loop Synology
**Objetivo**
Reducir ambigüedad entre deploy "parece bien" y deploy realmente verificable.

**Scope sugerido**
- mejorar artifact de sign-off o release gate
- destacar señales críticas de PASS/WARN/FAIL
- hacer más evidente qué revisar primero cuando algo sale mal

**Métrica a mover**
- tiempo hasta entender el estado del deploy
- calidad de la evidencia de sign-off

**Rollback**
- volver al formato/artifact anterior sin tocar el motor de trading

---

### PR-P2 — Observabilidad operativa orientada a decisión
**Objetivo**
Convertir el exceso de datos operativos en señales de decisión más claras.

**Scope sugerido**
- enriquecer resumen del command center o artifacts del gate
- resaltar drift, stale data, errores de reconcile o gaps de cobertura
- reducir lectura ambigua del estado real

**Métrica a mover**
- tiempo de diagnóstico operativo
- incidentes detectados tarde

**Rollback**
- revertir visualización/campos nuevos manteniendo APIs actuales si hace falta

---

### PR-P3 — Mejora puntual de workstation con impacto operativo real
**Objetivo**
Eliminar una ambigüedad concreta del operador dentro de la trading workstation.

**Scope sugerido**
- claridad de origen/frescura/severidad
- mejor lectura de trade plans degradados
- feedback más usable para acciones seguras tipo `reconcile now` / `refresh now`

**Métrica a mover**
- claridad del estado por operación
- reducción de clicks o inspección manual

**Rollback**
- revertir capa UI o wiring nuevo sin afectar payloads estables del backend

---

### PR-P4 — Cierre documental del ciclo piloto
**Objetivo**
Cerrar la ventana con evidencia, aprendizaje y siguiente decisión explícita.

**Scope sugerido**
- actualizar scoreboard
- actualizar decision log
- enlazar resultados en roadmap principal si corresponde
- preparar siguiente one bet o cerrar piloto

**Métrica a mover**
- continuidad y claridad del aprendizaje

**Rollback**
- no aplica; es cierre documental del ciclo

## Backlog explícito del piloto
Queda fuera de esta primera ventana salvo que una incidencia lo fuerce:

- cambios grandes de estrategia alpha
- expansión fuerte de backtesting
- reestructuras profundas de arquitectura
- live trading o cambios que acerquen producción real sin pasar por los gates ya definidos

## Criterio de cierre
La ventana se considera cerrada cuando:
- el one bet tiene resultado explícito,
- los PRs de la ventana están mergeados o descartados con razón clara,
- el scoreboard está actualizado,
- el decision log registra qué se mantiene y qué se ajusta del método.
