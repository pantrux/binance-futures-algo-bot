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
3. La numeración de ADRs debe ser única y monotónica; si aparece una colisión, renumerar el documento más nuevo y actualizar referencias antes del merge.
4. Cualquier cambio documental relevante debe reflejarse también en Outline.
5. Antes de mergear cambios documentales, la CI debe validar los links Markdown locales con `scripts/check_markdown_links.py`.
6. Para escribir en Outline, preferir el workflow manual de GitHub Actions o una corrida local explícita y controlada de `scripts/sync_outline_docs.py`; evitar automatizar pushes a Outline en cada commit.
7. Mantener títulos y contenido en español, salvo excepciones explícitas.

## Índices por carpeta

- `docs/adr/README.md`
- `docs/plans/README.md`
- `docs/diagrams/README.md`
- `docs/pr-plan/README.md`
