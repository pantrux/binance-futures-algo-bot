# Documentación del proyecto

Estructura oficial de documentación para mantener navegación simple y consistente.

## Estructura

- `adr/` — decisiones de arquitectura activas (ADRs)
  - `adr/archive/` — ADRs históricos o reemplazados
- `plans/` — planes, roadmap, piloto G-Stack, scoreboards, runbooks y documentos de operación
  - `plans/archive/` — planes históricos absorbidos por roadmaps más recientes
- `diagrams/` — diagramas y flujos Mermaid
- `pr-plan/` — gobernanza del flujo por Pull Requests

## Reglas de orden

1. Todo documento nuevo debe ir en la carpeta temática correcta.
2. Si un documento queda obsoleto o genera conflicto de numeración, se mueve a la carpeta de archivo correspondiente (`adr/archive/`, `plans/archive/`, etc.) en vez de mantenerse como activo.
3. Cualquier cambio documental relevante debe reflejarse también en Outline.
4. Antes de mergear cambios documentales, la CI debe validar los links Markdown locales con `scripts/check_markdown_links.py`.
5. Mantener títulos y contenido en español, salvo excepciones explícitas.

## Índices por carpeta

- `docs/adr/README.md`
- `docs/plans/README.md`
- `docs/diagrams/README.md`
- `docs/pr-plan/README.md`
