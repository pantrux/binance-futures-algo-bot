# Fase 15 — Hardening del harness operacional

## Propósito
Cerrar los detalles de robustez del harness de tests operacionales que aún pueden generar ruido, flakes o ambigüedad en CI, especialmente alrededor de fixtures shell/HTTP y teardown determinista.

## Objetivo de la fase
Dejar el carril de smoke/release con pruebas reproducibles, limpias y fáciles de depurar, para que el foco del proyecto vuelva a lógica de trading y no a fricción del harness.

## Entregables esperados
- tipado explícito en helpers de fixtures operacionales
- cierre determinista de threads/servidores fixture
- timeouts y cleanup consistentes en tests shell/end-to-end
- runbooks/roadmaps reflejando el cierre del bloque de observabilidad anterior

## PR inicial de la fase
### PR-70 — Cierre formal de Fase 14 + hardening final del fixture shell ✅
- tipar explícitamente `run_fixture_server`
- centralizar apagado del servidor fixture
- verificar que el thread realmente termina tras `join`
- actualizar roadmap/master-plan/PR roadmap para marcar Fase 14 como cerrada y Fase 15 como activa
- documentar cierre formal en `phase14-observability-closure.md`
- mergeado en `6f5a580`

### PR-71 — Cobertura shell para payload inválido del command center ✅
- agregar caso end-to-end donde `/dashboard/command-center` devuelve payload inválido
- validar que `synology_smoke_test.sh` falle propagando el error del helper de contexto
- actualizar roadmap/master-plan/PR roadmap con el nuevo frente activo
- mergeado en `5204364`

### PR-72 — Cobertura shell para fallos HTTP base ✅
- agregar casos end-to-end para `/health` no-200 y `/metrics` inesperado sin auth
- validar que el shell smoke falle con mensajes claros en `stderr`
- extender el fixture HTTP local con overrides por ruta para failure modes reproducibles
- mergeado en `43c1c1c`

### PR-73 — Cobertura shell para summary y trade-plans ✅
- agregar casos end-to-end para `/dashboard/summary` no-200 y `/trade-plans` no-200
- validar que el shell smoke falle con mensajes claros en `stderr` para ambos casos
- mergeado en `23400e5`

### PR-74 — `/metrics` autenticado + cleanup de helpers del fixture ✅
- cubrir el camino de `/metrics` con `METRICS_API_KEY` presente
- validar header `x-metrics-key` correcto/incorrecto desde el fixture local
- limpiar duplicación menor en helpers del fixture si mejora legibilidad y mantenimiento
- mantener el smoke shell totalmente reproducible sin dependencia del NAS real también en el camino autenticado de métricas
- mergeado en `ba68d86`

### PR-75 — Cobertura shell para strictness de `testnet/ping` ✅
- cubrir el branch `STRICT_EXTERNAL_CHECKS=false` cuando `/integrations/binance/testnet/ping` falla
- cubrir el branch `STRICT_EXTERNAL_CHECKS=true` para asegurar fallo explícito
- mantener el harness reproducible sin depender de Binance real
- mergeado en `6e4bbd7`

### PR-76 — Failure modes de `WEB /` en el shell smoke ✅
- cubrir el caso donde la home web responde `non-200`
- cubrir el caso donde la home web responde `200` pero con body vacío
- mantener el harness reproducible y el diagnóstico claro para fallos de `fetch_body()`/marcadores web
- mergeado en `72dba40`

### PR-77 — Marcadores faltantes de `WEB /` en el shell smoke ✅
- cubrir el caso donde la home responde `200` pero falta el marcador base `bot`
- cubrir el caso donde la home responde `200` pero falta un marcador central del command center
- mantener el harness reproducible y el diagnóstico claro para fallos de `check_body_contains()`
- mergeado en `eae04f3`

### PR-78 — Marcadores adicionales de `WEB /` en el shell smoke 🟡
- cubrir el caso donde la home responde `200` pero falta `Detalle por trade plan`
- cubrir el caso donde la home responde `200` pero falta `Reconcile actual`
- mantener el harness reproducible y el diagnóstico claro para fallos adicionales de `check_body_contains()`

## Criterio de cierre
- no deben quedar hilos/threads fixture vivos silenciosamente tras los tests
- la documentación debe distinguir con claridad Fase 14 cerrada vs Fase 15 activa
- CI debe seguir verde sin depender del NAS real para validar el contrato del smoke
