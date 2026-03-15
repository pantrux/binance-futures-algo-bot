# Fase: hardening de ingesta de mercado

## Objetivo
Corregir los bloqueantes detectados en review sobre la ingesta de mercado antes de construir indicadores encima.

## Correcciones
- BigInteger para timestamps Binance en ms
- rollback explícito en el servicio
- unique constraint compuesto para evitar duplicados concurrentes
- paralelización de requests HTTP independientes

## Resultado esperado
Base de mercado segura y apta para continuar con indicadores técnicos.
