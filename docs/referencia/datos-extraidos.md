# Datos extraídos

El resultado utiliza un contrato cerrado. Un proveedor no puede añadir campos
arbitrarios.

## Documento

| Campo | Descripción |
|---|---|
| Tipo | Factura de proveedor, abono, otro o desconocido |
| Referencia | Número visible de factura o documento |
| Emisión | Fecha ISO cuando es válida |
| Vencimiento | Fecha ISO cuando es válida |
| Moneda | Código de moneda |
| Referencia de pago | Referencia visible |
| Clase de gasto | Orientación no contable |
| Indicio fiscal | Orientación no vinculante |
| Confianza | Valor entre 0 y 1 |
| Alertas | Incidencias detectadas |

## Proveedor

- nombre;
- NIF/VAT;
- correo;
- IBAN.

El IBAN y correo se extraen como evidencia, pero no se escriben en la ficha del
proveedor.

## Destinatario

- nombre impreso;
- NIF/VAT impreso.

Odoo compara el identificador impreso con la empresa. Una diferencia bloquea la
aplicación automática al borrador.

## Importes

- neto;
- impuesto;
- total.

Se comprueba que neto más impuesto coincide con total con una tolerancia de
cinco céntimos. Cuando existen líneas, también se compara su suma con el neto.

## Líneas

Cada línea incluye:

- concepto;
- cantidad;
- precio unitario;
- importe neto;
- porcentaje de impuesto si aparece;
- porcentaje de descuento si aparece.

El módulo admite hasta 200 líneas y no elige automáticamente la cuenta contable
ni el impuesto de Odoo.

## Clases de gasto

El modelo puede sugerir software/IA, telecomunicaciones, suscripciones,
seguridad social, servicios profesionales, transporte, oficina, seguros,
gastos bancarios, otros servicios o desconocido.

La categoría es informativa y no sustituye el plan contable de la empresa.

## Indicios fiscales

Puede indicar operación nacional deducible o no deducible, inversión del sujeto
pasivo UE o no UE, exenta, no sujeta o desconocida. La decisión fiscal siempre
corresponde a la revisión contable.
