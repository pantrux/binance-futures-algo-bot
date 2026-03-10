# ADR-002 — Risk Engine como guardián único

## Estado
Aceptado

## Decisión
Toda operación debe pasar por un **RiskEngine** centralizado e ineludible.

## Reglas obligatorias
- Riesgo total agregado <= 5% del capital.
- Riesgo por trade recomendado: 0.5% a 1.0%.
- Tope duro por trade: 1.25%.
- Circuit breakers diarios/semanales.
- Prohibición de entrada si el score o el régimen son desfavorables.

## Consecuencias
- Las estrategias no calculan tamaño final.
- La ejecución solo recibe planes ya aprobados por riesgo.
- Los cambios al motor de riesgo deben requerir tests y revisión estricta.
