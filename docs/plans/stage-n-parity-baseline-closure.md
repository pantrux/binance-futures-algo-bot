# Cierre de baseline — Etapa N (Refinamiento de paridad paper vs testnet)

## Objetivo
Formalizar el cierre de la baseline inicial de Etapa N, dejando consistente que los reportes de paridad/shadow run ya no mezclan temporalidades de forma ambigua y que los operadores pueden consultar snapshots agregados y puntuales con semántica alineada.

## Criterios de cierre
- [x] `shadow run` no cruza trade plans de distinta `timeframe`
- [x] `execution parity` no cruza trade plans de distinta `timeframe`
- [x] `/execution/parity/{symbol}` soporta filtro opcional por `timeframe`
- [x] `/reporting/shadow-run-summary` soporta filtro opcional por `timeframe`
- [x] `symbols` en `shadow-run-summary` se desambigüa por `(symbol, timeframe)`
- [x] tests de servicio y ruta cubren los nuevos contratos
- [x] ADR-032 y roadmap quedaron alineados con la baseline alcanzada

## PRs que cerraron la baseline
- `PR-82` — emparejamiento shadow run sensible a `timeframe`
- `PR-83` — execution parity sensible a `timeframe`
- `PR-84` — sincronización inicial del roadmap tras baseline de Etapa N
- `PR-85` — cierre de desfase documental residual tras `PR-84`
- `PR-86` — filtro por `timeframe` en execution parity
- `PR-87` — filtro por `timeframe` en shadow-run-summary
- `PR-88` — breakdown por `timeframe` en `shadow-run symbols`

## Resultado logrado
La baseline inicial de Etapa N deja una semántica consistente para consumo operativo:
- el reporte puntual de parity y el resumen agregado de shadow run ya comparten criterio por `timeframe`
- los snapshots ya no mezclan métricas de distintas temporalidades bajo una misma fila ambigua
- cuando un símbolo opera en más de una temporalidad, la API permite ver el detalle sin cruces silenciosos

## Qué NO resuelve todavía
- matching más fino para estrategias multi-entrada dentro de una misma `timeframe`
- filtros más específicos por ventana/estrategia/tag si en el futuro aparecen múltiples variantes concurrentes del mismo símbolo y temporalidad
- cierres/alertas operativas basadas en desviación de parity, que serían un carril aparte de producto/operación

## Próximo foco recomendado
Volver a iniciativas de producto/trading con impacto directo y reabrir Etapa N sólo si aparece una necesidad operativa nueva (por ejemplo multi-strategy parity o alertas automáticas por desviación).
