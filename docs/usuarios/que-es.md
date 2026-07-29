# Qué es AI Processing

AI Processing es un asistente documental para facturas de proveedor en Odoo.
Puede trabajar con OpenAI, OpenRouter, Ollama local o Cloud y servidores propios
compatibles.

## Qué hace

- recibe PDF, JPEG, PNG y WebP;
- admite varios adjuntos en un mismo correo;
- separa cada adjunto como un trabajo independiente;
- detecta facturas, abonos y archivos que no son facturas;
- extrae proveedor, NIF/VAT, referencia, fechas, moneda, conceptos e importes;
- comprueba coherencia aritmética y destinatario;
- mantiene el historial del modelo utilizado y sus intentos;
- prepara datos para un borrador de factura de proveedor.

## Qué no hace

- no contabiliza ni publica facturas;
- no inicia pagos;
- no decide la deducibilidad fiscal;
- no crea proveedores, impuestos, cuentas o bancos;
- no sustituye la revisión del documento original;
- no garantiza que el proveedor o el modelo hayan emitido datos correctos.

## Quién puede usarlo

Los usuarios con permisos de facturación pueden consultar la bandeja, procesar
documentos y revisar borradores. La configuración del proveedor, claves,
modelos y políticas corresponde a administradores de Odoo.

La información está aislada por empresa. Antes de trabajar, compruebe que está
seleccionada la compañía correcta en Odoo.
