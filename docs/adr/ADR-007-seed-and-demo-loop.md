# ADR-007 — Seed y demo loop para validación operativa inicial

## Estado
Aceptado

## Decisión
Incorporar un loop de demostración controlado que genere trade plans de ejemplo y, si corresponde, los ejecute en paper trading para validar el flujo end-to-end.

## Justificación
- Permite validar rápidamente el dashboard y la persistencia.
- Acelera QA inicial en Synology.
- Reduce tiempo de integración mientras llegan datos de mercado reales.

## Consecuencias
- El worker dispone de un `DemoSignalService`.
- Se añade un script de seed para poblar datos operativos de ejemplo.
- Este loop es solo para validación; no sustituye señales reales de mercado.
