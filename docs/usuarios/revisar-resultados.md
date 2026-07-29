# Revisar y aplicar resultados

## Abrir el resultado

Desde **Bandeja de facturas**, abra el correo y después **Abrir borrador** en el
documento correspondiente. También puede abrir una factura de proveedor en
borrador y consultar la pestaña **AI Processing**.

## Lista de comprobación obligatoria

Compare el PDF original con Odoo:

- tipo de documento: factura, ticket o abono;
- nombre y NIF/VAT del proveedor;
- nombre y NIF/VAT del destinatario;
- número o referencia de factura;
- fecha de emisión y vencimiento;
- moneda;
- referencia de pago;
- todos los conceptos, cantidades, precios y descuentos;
- base imponible, impuestos y total;
- posible duplicidad;
- avisos y nivel de confianza.

## Qué significa “Aplicar al borrador”

El botón copia al borrador únicamente los campos permitidos y las líneas
extraídas. No publica el asiento ni realiza el pago.

Para aplicarlo:

1. La factura debe seguir en borrador.
2. El adjunto principal debe ser el mismo que se analizó.
3. El destinatario no puede estar marcado como incorrecto.
4. No debe existir un duplicado bloqueante.
5. Debe existir un proveedor cuyo NIF/VAT coincida exactamente.
6. El borrador no puede contener líneas comerciales previas.

Si ya existen líneas, el módulo las conserva. El usuario debe decidir
manualmente si las elimina antes de aplicar la extracción.

## Después de aplicar

Revise de nuevo los campos contables que la IA no decide:

- cuenta de gasto;
- impuestos y posición fiscal;
- deducibilidad;
- dimensiones analíticas;
- periodo contable;
- condiciones y método de pago;
- retenciones, inversión del sujeto pasivo o reglas especiales.

Solo después siga el procedimiento habitual de validación y contabilización de
su organización.
