# Monitorización diaria

## Qué revisar

- documentos pendientes y antigüedad de la cola;
- documentos fallidos;
- correos parcialmente completos;
- uso exitoso del respaldo;
- tiempo por modelo;
- errores repetidos por categoría;
- cambios de disponibilidad del catálogo;
- consumo y presupuesto en el proveedor.

## Indicadores de la configuración

La pantalla principal muestra:

- **Pendientes**: documentos en cola o procesamiento;
- **Procesadas**: facturas o archivos clasificados como otros;
- **Rescates**: intentos correctos del modelo de respaldo;
- **Fallos**: intentos fallidos acumulados.

Un aumento de rescates indica que el principal necesita revisión aunque el
usuario reciba resultados finales.

## Historial

En **Contabilidad → AI Processing → Historial** se registra:

- fecha de inicio y fin;
- documento y borrador;
- protocolo y modelo;
- rol principal o respaldo;
- éxito o fallo;
- duración;
- categoría y mensaje seguro.

No se debe sustituir este historial por respuestas completas del proveedor en
logs generales.

## Trabajos interrumpidos

Un documento reservado durante más de 20 minutos vuelve automáticamente a la
cola. Si se repite, revise reinicios, memoria, conectividad y tiempo máximo.

## Revisión periódica

Semanalmente:

- revise fallos y rescates;
- compruebe costes;
- pruebe una factura conocida;
- verifique copia de seguridad;
- revise avisos de dependencias.

Mensualmente:

- evalúe exactitud por campo y proveedor;
- confirme permisos;
- revise retención del proveedor;
- retire modelos o claves que ya no se usan.
