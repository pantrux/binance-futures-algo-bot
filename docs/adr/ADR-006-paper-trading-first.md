# ADR-006 — Paper trading antes de cualquier ejecución real

## Estado
Aceptado

## Decisión
Toda ejecución inicial del sistema debe pasar por una capa de `paper trading` que cree órdenes, posiciones y eventos de riesgo simulados antes de habilitar integración real de ejecución.

## Justificación
- Validar el pipeline end-to-end sin exponer capital.
- Auditar la transición plan -> orden -> posición.
- Detectar errores de sizing, estado o documentación sin tocar Binance real.

## Consecuencias
- Se crea `PaperTradingService` como ejecutor inicial.
- La API expone una ruta de ejecución simulada.
- El dashboard debe reflejar conteos de planes, ejecuciones simuladas y posiciones abiertas.
