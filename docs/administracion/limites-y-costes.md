# Límites y costes

Los límites reducen exposición, consumo accidental y saturación. No deben
tratarse únicamente como ajustes de rendimiento.

## Controles disponibles

| Control | Protege frente a |
|---|---|
| Tamaño máximo | Archivos enormes o consumo de memoria |
| Páginas PDF | Documentos desproporcionados |
| Páginas visuales | Coste de visión en Ollama y servidores compatibles |
| Tiempo máximo | Peticiones bloqueadas |
| Correos por minuto | Ráfagas de entrada |
| Adjuntos por correo | Mensajes abusivos o accidentales |
| Tokens de salida | Respuestas excesivas |
| Umbral de confianza | Resultados que requieren atención |

## Ajuste seguro

1. Empiece con los valores recomendados.
2. Mida percentiles de tamaño, páginas, duración y tokens.
3. Investigue los casos que exceden límites.
4. Modifique un control cada vez.
5. Repita las pruebas del modelo principal y de respaldo.

## Coste

El módulo registra intentos, modelo, rol y duración, pero el coste definitivo
depende del proveedor. Compare los registros de Odoo con la facturación del
servicio.

Una activación automática debe incluir alertas externas de presupuesto y
límites del proveedor. El modelo de respaldo también puede generar coste.
