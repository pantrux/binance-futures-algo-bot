# Plan maestro de diseño e implementación

## Visión
Construir un bot algorítmico de Binance Futures con decisiones explicables, ejecución controlada y trazabilidad documental completa.

## Capacidades obligatorias
- análisis técnico
- análisis fundamental crypto-native
- análisis de sentimiento
- scalping e intradía
- indicadores principales
- patrones de velas y estructura
- sizing dinámico
- gestión de riesgo estricta
- dashboard web
- documentación automática en Outline

## Arquitectura lógica
1. Ingesta de datos
2. Normalización de señales
3. Clasificador de régimen
4. Estrategias
5. Risk Engine
6. Executor
7. Persistencia
8. Dashboard
9. Sync documental

## Estrategias de la primera ola
- scalping de continuación
- scalping de reversión controlada
- breakout intradía
- mean reversion intradía

## Reglas de producción
- nunca exceder 5% de riesgo total agregado
- operar primero en paper trading
- luego testnet
- luego capital real mínimo
- cualquier cambio de riesgo requiere tests y documentación

## Definition of Done del MVP
- API operativa
- worker con score compuesto y blueprint de trade
- dashboard base
- CI verde
- documentos principales en Outline
- repositorio público/privado creado en GitHub
