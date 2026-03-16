# ADR-037 — Command center como trading workstation modular

## Contexto
El command center actual consolidó suficiente información operacional (planes, órdenes, posiciones, riesgo, reconciliación, shadow run), pero su presentación seguía demasiado monolítica: demasiada densidad en una sola homepage, poco drill-down real y jerarquía visual más cercana a un reporte largo que a una terminal operativa.

## Decisión
Se redefine la siguiente iteración del command center como una **trading workstation modular**, con estas reglas:

1. La homepage deja de intentar mostrar todo a la vez.
2. La UI se organiza en una **shell** con:
   - navegación explícita por secciones,
   - overview compacto arriba,
   - paneles especializados al medio,
   - drill-down por operación al fondo.
3. El detalle profundo pasa a ser **plegable/navegable** por operación en vez de exponer toda la información abierta por defecto.
4. La iteración inicial se enfoca en **arquitectura visual y navegación**.
5. El realtime duro (polling corto, SSE o websocket) queda fuera de este corte para no mezclar transporte de datos con re-arquitectura visual.

## Consecuencias positivas
- La UI se acerca más a una mesa de trading profesional que a un dashboard monolítico.
- Menor fatiga visual para operación diaria.
- Mejor base para agregar realtime encima sin rehacer otra vez la estructura.
- Mejor jerarquía entre overview, monitoring y cockpit detallado.

## Consecuencias negativas
- La primera iteración de workstation no entrega aún streaming/realtime real.
- Requiere adaptar hábitos de navegación respecto al command center anterior.
- Puede exigir una segunda iteración para modularizar también componentes React internos si la vista sigue creciendo.

## Futuro explícito
Siguientes expansiones esperables sobre esta base:
- ticker/price tape con actualización periódica,
- mark price / PnL vivos,
- tabs o drawers más ricos por operación,
- watchlists y order blotter más parecidos a plataformas tipo desk.
