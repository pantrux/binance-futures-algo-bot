# ADR-039 — Links navegables en Outline

## Estado
Propuesto

## Contexto
La documentación del proyecto se sincroniza desde el repositorio hacia Outline mediante `scripts/sync_outline_docs.py`. Varios documentos contienen links relativos a otros archivos del repo (por ejemplo `./otro-doc.md`).

Al publicar ese Markdown en Outline, esos links dejan de apuntar al filesystem/repo local y pueden quedar rotos o ambiguos si no se reescriben a URLs navegables.

## Decisión
Durante la sincronización a Outline:

1. Los links a documentos que también existen como documentos sincronizados en Outline se reescriben para apuntar a la **URL del documento en Outline**.
2. Los links a archivos locales del repositorio que **no** tienen equivalente en Outline se reescriben a la **URL web del repositorio** (GitHub `blob/<ref>`).
3. Los links externos (`https`, `mailto`, etc.) y anchors internos (`#...`) se preservan sin cambios.

## Justificación
- Mantiene navegación útil desde Outline.
- Evita depender de rutas locales de OpenClaw o `file://`.
- No requiere infraestructura adicional para el caso base de documentación versionada.
- Deja un fallback estable para archivos del repo no publicados como documentos Outline.

## Consecuencias
- `scripts/sync_outline_docs.py` necesita una segunda pasada para reescribir links con URLs reales.
- La URL base web del repo debe poder derivarse desde `remote.origin.url` o configurarse por variable de entorno.
- Para artefactos no versionados (PDFs/reportes generados), seguirá siendo recomendable una estrategia aparte de publicación HTTP o storage.

## Variables operativas
- `OUTLINE_REPO_WEB_BASE` (opcional): fuerza la base web del repo.
- `OUTLINE_GIT_REF` (opcional, default `main`): ref usada para links `blob/<ref>`.

## Alternativas consideradas
1. Mantener links locales tal cual. Rechazada: se rompen fuera del host.
2. Usar solo GitHub para todos los links. Rechazada: pierde navegación interna de Outline cuando el documento sí existe allí.
3. Exponer el filesystem de OpenClaw vía `file://` o similar. Rechazada: frágil y poco portable.
