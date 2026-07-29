# Solución de problemas

## El correo no aparece

Compruebe, en este orden:

1. que la pasarela recibió el mensaje;
2. que SPF, DKIM o DMARC no lo rechazaron;
3. que el dominio de alias es correcto;
4. que el alias pertenece a la empresa seleccionada;
5. que el dominio del remitente está permitido;
6. los logs del sistema de correo de Odoo.

## El adjunto aparece como ignorado

Abra el documento y lea **Motivo de decisión**. Las causas habituales son:

- formato no admitido;
- firma binaria distinta de la extensión;
- archivo vacío, corrupto o demasiado grande;
- imagen demasiado pequeña;
- PDF con demasiadas páginas;
- límite de adjuntos del correo superado.

## “La variable de entorno de la clave no es válida”

Escriba el nombre de la variable, no la clave. Debe comenzar por letra
mayúscula o `_` y contener únicamente mayúsculas, números y guion bajo:

```text
OLLAMA_API_KEY
OPENAI_API_KEY
OPENROUTER_API_KEY
```

Después configure el valor secreto en el entorno del proceso Odoo y reinicie el
servicio si la plataforma lo requiere.

## No se puede guardar una clave pegada

El servidor necesita una clave Fernet válida en `AI_PROCESSING_MASTER_KEY`.
Se recomienda configurar directamente la clave del proveedor como secreto de
entorno en lugar de pegarla.

## La conexión funciona pero el modelo no aparece

- vuelva a leer el catálogo;
- compruebe que el protocolo coincide con la API;
- revise si el modelo fue marcado como no disponible;
- confirme permisos de la clave;
- consulte la respuesta del endpoint de catálogo sin guardar secretos.

## El modelo aparece pero no se puede seleccionar

Ejecute **Probar visión**. Si falla:

- confirme que el modelo acepta imágenes;
- revise el formato que espera el servidor;
- compruebe tokens y contexto;
- pruebe otro modelo.

La aprobación manual debe ser una excepción documentada.

## Un endpoint privado está bloqueado

Las direcciones privadas se bloquean por defecto. Si el servidor es realmente
interno y controlado, active **Permitir endpoint de red privada** y verifique
antes la ruta y la autenticación.

## El documento queda pendiente

- compruebe que la tarea programada está activa;
- revise el límite de correos por minuto;
- confirme que no hay otro trabajador procesándolo;
- busque fallos del cron;
- espere la recuperación automática si el trabajo fue interrumpido.

## La extracción falla y no usa respaldo

El respaldo no actúa ante errores de autenticación, consentimiento, permisos,
seguridad o archivo. Corrija primero la causa indicada.

## No aparece “Aplicar al borrador”

Compruebe:

- factura todavía en borrador;
- resultado listo o con aviso revisable;
- mismo adjunto principal;
- destinatario compatible;
- ausencia de duplicado;
- proveedor existente con NIF/VAT exacto.

## No se puede aplicar porque existen líneas

El módulo conserva las líneas previas. Revise su origen y elimínelas
manualmente solo si corresponde; después vuelva a aplicar.

## Escalado a soporte

Incluya:

- versión del módulo y de Odoo;
- hora y empresa;
- estado del correo y documento;
- categoría y mensaje seguro;
- protocolo y modelo;
- pasos para reproducir.

No incluya claves ni el documento real. Use una copia redactada o una factura
de prueba cuando sea posible.
