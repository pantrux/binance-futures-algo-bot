# Binance Futures Algo Bot

Bot de trading algorítmico para **Binance USDⓈ-M Futures** orientado a operativa automática de **scalping** e **intradía**, con enfoque de arquitectura auditable, gestión de riesgo estricta y documentación viva en Outline.

## Objetivos del MVP

- Análisis técnico, fundamental y de sentimiento.
- Detección de velas japonesas y patrones.
- Clasificación de régimen de mercado.
- Gestión dinámica de exposición por operación.
- Regla de oro de riesgo: **nunca arriesgar más del 5% del capital total**.
- Frontend web para observabilidad y métricas.
- Documentación automática de planes operativos en Outline.

## Arquitectura del monorepo

- `apps/api`: API FastAPI + endpoints de salud, mercado, riesgo y planes.
- `apps/worker`: motor de análisis/estrategias/riesgo y sincronización documental.
- `apps/web`: dashboard web en Next.js.
- `packages/shared`: contratos compartidos y documentación de payloads.
- `docs`: ADRs, diagramas, roadmap y especificaciones.
- `infra`: Docker, GitHub, despliegue y observabilidad.

## Estado actual

## Restricción de infraestructura

Todo el runtime productivo del proyecto debe desplegarse en el **NAS Synology** mediante contenedores. El servidor de OpenClaw **no** es un host válido para producción de este bot.

## Requisitos mínimos de runtime

- `apps/api`: Python 3.12 (Dockerfile basado en `python:3.12-slim`)
- `apps/worker`: **Python 3.11+** (actualmente desplegado con `python:3.12-slim`)
- `apps/web`: Node.js 22

El worker market-driven usa `asyncio.TaskGroup`; si se intenta ejecutar con Python < 3.11 debe fallar explícitamente al iniciar.

Este repositorio contiene la **fundación del proyecto**:

- blueprint de arquitectura
- ADRs iniciales
- motor base de riesgo
- agregador de señales
- clasificador de régimen
- cliente inicial de Outline
- API base
- dashboard base
- pipeline CI/CD inicial

## Regla de riesgo crítica

El sistema incorpora límites multicapa:

- riesgo por trade
- riesgo agregado simultáneo
- pérdida diaria
- pérdida semanal
- circuit breaker

> Ninguna estrategia puede saltarse el `RiskEngine`.

## Próximos hitos

1. Integración Binance Futures Testnet
2. Persistencia PostgreSQL + Alembic
3. Websockets de mercado
4. Backtesting / paper trading
5. Sincronización completa con Outline
6. Alertas y observabilidad avanzada

## Documentación

Toda la documentación del proyecto está en español dentro de `docs/` y debe sincronizarse también en Outline.

## Workflow GitHub

A partir de la fase actual, el proyecto opera con **branches + Pull Requests**.
La hoja de ruta formal de PRs está en `docs/pr-plan/PR_ROADMAP.md`.
