# ADR-004 — Synology NAS como runtime único

## Estado
Aceptado

## Decisión
Todo el runtime productivo del proyecto debe ejecutarse dentro del NAS Synology usando contenedores. OpenClaw se usa solo para coordinación, documentación y soporte de desarrollo.

## Justificación
- Aislamiento operativo.
- Persistencia centralizada en infraestructura controlada.
- Coherencia con el resto del stack doméstico/privado del usuario.
- Menor riesgo de mezclar herramientas de asistencia con runtime de trading.

## Consecuencias
- Todo despliegue debe generar artefactos compatibles con Docker/Container Manager.
- Las rutas de datos persistentes deben apuntar a volúmenes del NAS.
- La documentación de infraestructura debe mantenerse sincronizada en Outline.
