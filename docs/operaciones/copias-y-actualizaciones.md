# Copias y actualizaciones

## Copias de seguridad

La base de datos y el filestore forman una unidad. Una copia incompleta puede
conservar los registros sin los PDF, o los PDF sin sus relaciones.

Antes de actualizar:

1. copie base de datos y filestore;
2. registre versión actual y configuración;
3. confirme que la restauración está probada;
4. conserve el commit desplegado;
5. detenga temporalmente la entrada automática si el cambio lo requiere.

Las claves almacenadas solo en el entorno no forman parte de la base de datos.
Documente cómo restaurarlas desde el gestor de secretos.

## Actualización segura

1. Revise cambios y dependencias en una rama.
2. Ejecute pruebas unitarias e integración Odoo.
3. Pruebe copia de una base representativa sin correo real.
4. Valide catálogo, sonda y una factura conocida.
5. Despliegue desde una release verificada o desde una revisión fijada del repositorio.
6. Compruebe cola, logs y borrador.
7. Mantenga un procedimiento de reversión.

No pruebe una actualización publicando o pagando automáticamente una factura.

## Cambio de modelo o proveedor

Trátelo como un cambio funcional:

- confirme condiciones de privacidad;
- evalúe un conjunto estable de documentos;
- compare exactitud por campo;
- revise coste y latencia;
- pruebe el respaldo;
- registre la fecha del cambio.
