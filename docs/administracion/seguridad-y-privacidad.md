# Seguridad y privacidad

## Datos que pueden salir de Odoo

Al autorizar la transferencia, el servicio seleccionado puede recibir el PDF o
las imágenes renderizadas. Una factura puede contener identidad, NIF/VAT,
direcciones, datos bancarios, precios y relaciones comerciales.

Antes de activar el servicio, determine:

- responsable y encargado del tratamiento;
- finalidad y base jurídica;
- región de procesamiento;
- retención y uso para entrenamiento;
- subencargados;
- medidas técnicas;
- procedimiento de ejercicio de derechos e incidentes.

## Claves

Orden recomendado:

1. variable de entorno en el proceso Odoo;
2. secreto gestionado por la plataforma de despliegue;
3. clave cifrada en base de datos con `AI_PROCESSING_MASTER_KEY`.

Nunca incluya claves en Git, documentación, prompts, facturas, correos,
capturas, incidencias o registros.

Rote inmediatamente cualquier clave expuesta y compruebe el historial de uso.

## Servidores internos

Por defecto se bloquean loopback, direcciones privadas y link-local para evitar
peticiones del servidor hacia destinos imprevistos.

La opción de endpoint privado elimina esa barrera para el perfil. Antes de
activarla:

- verifique DNS y dirección;
- limite rutas de salida;
- autentique el servicio;
- use TLS cuando atraviese redes no confiables;
- impida redirecciones;
- supervise solicitudes.

## Permisos y empresas

Solo usuarios contables gestionan la bandeja y los borradores. Solo
administradores configuran proveedores y aprueban modelos manualmente.

Compruebe las reglas multiempresa y evite conceder acceso administrativo para
resolver tareas de revisión ordinaria.

## Correo

Una lista de dominios no demuestra quién envió el mensaje. Exija SPF, DKIM y
DMARC en la pasarela y defina cuarentena o rechazo para fallos.

## Incidentes

No abra incidencias públicas con facturas o respuestas completas. Redacte NIF,
IBAN, nombres, correos, referencias y claves. Conserve evidencia suficiente
para investigar sin copiar datos innecesarios.
