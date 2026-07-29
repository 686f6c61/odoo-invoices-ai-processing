# Manual de AI Processing

AI Processing recibe facturas y notas de abono, extrae sus datos con un modelo
de IA y prepara un borrador para revisión humana en Odoo 19.

La IA aporta evidencia. La persona responsable conserva siempre la decisión
contable: el módulo no publica asientos, no paga facturas y no crea proveedores,
cuentas, impuestos ni datos bancarios.

## Elija su recorrido

| Perfil | Empiece aquí |
|---|---|
| Usuario que envía facturas | [Enviar facturas por correo](usuarios/enviar-facturas.md) |
| Usuario de contabilidad | [Revisar y aplicar resultados](usuarios/revisar-resultados.md) |
| Administrador de Odoo | [Configuración inicial](administracion/configuracion-inicial.md) |
| Responsable técnico | [Proveedores y servidores propios](administracion/proveedores.md) |
| Soporte u operaciones | [Solución de problemas](operaciones/solucion-de-problemas.md) |

## Flujo general

1. El usuario envía uno o varios documentos al alias configurado.
2. Odoo conserva cada adjunto y comprueba su formato, tamaño y duplicidad.
3. Cada documento válido entra en una cola independiente.
4. El modelo principal intenta extraer los datos; el modelo de respaldo actúa
   solamente ante fallos recuperables.
5. Odoo valida estructura, importes, destinatario y posibles duplicados.
6. Contabilidad revisa la evidencia y decide si la aplica a un borrador.
7. La contabilización y el pago siguen el circuito normal de Odoo.

## Principios importantes

- No envíe una factura a un servicio externo sin autorización para transferirla.
- No confunda una extracción correcta con una contabilización correcta.
- Compruebe siempre proveedor, NIF/VAT, referencia, conceptos, impuestos,
  moneda, fechas y totales.
- Utilice dominios de remitente permitidos y autenticación SPF, DKIM y DMARC.
- Las claves deben permanecer en el entorno del servidor, nunca en Git,
  documentación, correos o capturas.

## Alcance de este manual

Este manual cubre el uso, configuración y operación del módulo. La instalación
de Odoo, la administración general del correo y las obligaciones fiscales de
cada empresa siguen siendo responsabilidad de sus especialistas.
