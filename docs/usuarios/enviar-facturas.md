# Enviar facturas por correo

## Formatos admitidos

- PDF;
- JPEG;
- PNG;
- WebP.

GIF, hojas de cálculo, documentos Word, archivos comprimidos, firmas e imágenes
demasiado pequeñas se conservan, pero no se procesan.

## Qué cuenta debe usar

Puede enviar la factura desde cualquier cuenta cuyo dominio haya autorizado el
administrador. AI Processing no selecciona ni exige una cuenta remitente
concreta.

Para el destino, use la dirección compartida indicada por su organización, por
ejemplo `facturas@empresa.com`. No envíe facturas al correo personal de quien
las revisa. Si el administrador todavía no ha preparado esa dirección, debe
seguir [Elegir y conectar el correo](../administracion/correo.md).

## Cómo preparar el correo

1. Use una dirección de remitente autorizada.
2. Escriba un asunto identificable, por ejemplo
   `Facturas proveedor - julio 2026`.
3. Adjunte cada factura como archivo separado.
4. No incruste la única copia de la factura en el cuerpo del correo.
5. Envíe el mensaje al alias indicado por el administrador.

El cuerpo del correo no se utiliza para dar instrucciones al modelo. Si necesita
explicar una excepción, hágalo para la persona revisora; no espere que cambie la
extracción.

## Varios adjuntos

Un mensaje puede contener varias facturas. Cada archivo válido se procesa de
forma independiente, por lo que el fallo de uno no cancela los demás.

El administrador define un máximo de adjuntos procesables por correo. Los que
superen el límite se conservarán con una explicación y no se enviarán al modelo.

## Duplicados

El módulo calcula una huella SHA-256 del archivo. Si la misma empresa ya recibió
el mismo archivo, el nuevo documento se marca como duplicado.

Cambiar el nombre del fichero no evita esta comprobación. Un PDF regenerado
puede tener otra huella, por lo que también se compara proveedor y referencia
cuando existen datos suficientes.

## Si el correo no aparece

Espere el tiempo normal de recogida de correo de Odoo y después consulte
[Solución de problemas](../operaciones/solucion-de-problemas.md). No reenvíe
repetidamente el mismo mensaje sin comprobar antes la pasarela.
