# ADR-001 — Stack base del proyecto

## Estado
Aceptado

## Decisión
Usar un stack híbrido:

- **Python + FastAPI** para API, motor cuantitativo y workers.
- **Next.js + TypeScript** para frontend web.
- **PostgreSQL** para persistencia operativa y analítica.
- **Redis** para colas, caché y coordinación de workers.
- **GitHub Actions** para CI/CD.
- **Outline** como repositorio oficial de documentación operativa y planes de trade.

## Justificación
Python maximiza velocidad de desarrollo para análisis cuantitativo y librerías financieras; Next.js acelera un panel moderno y mantenible.

## Consecuencias
- Se adopta monorepo con contratos claros entre API, worker y frontend.
- Se requiere hardening explícito para no mezclar lógica de señal con lógica de riesgo.
