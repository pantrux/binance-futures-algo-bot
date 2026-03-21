# Synology Deploy Evidence

## Identificación del despliegue
- Fecha/hora UTC:
- Operador:
- Commit SHA desplegado:
- Rama/ref origen:
- Motivo del despliegue:

## Entorno objetivo
- NAS / host:
- Directorio del proyecto en NAS:
- Compose file:
- ENV file usado:
- API pública:
- Web pública:
- API interna Docker:
- Web interna Docker:

## Evidencia de contenedores
- `docker compose ps` adjunto: sí/no
- `docker compose images` adjunto: sí/no
- Servicios esperados:
  - postgres
  - redis
  - migrate
  - api
  - worker
  - web

## Worker one-shot
- Corrida esperada del worker ejecutada: sí/no
- Resultado observado (`Exited (0)` / otro):
- Método de relanzamiento usado (si aplica):
- Evidencia/log relevante:

## Gates operativos
- Preflight: pass/fail
- Smoke: pass/fail
- Release gate: pass/fail
- JSON verify: pass/fail
- Shadow run gate (si aplica): pass/fail

## Documentación
- Docs locales actualizadas: sí/no
- Outline sincronizado: sí/no
- Evidencia del sync adjunta: sí/no

## Observaciones
- Riesgos conocidos:
- Rollback plan:
- Notas adicionales:
