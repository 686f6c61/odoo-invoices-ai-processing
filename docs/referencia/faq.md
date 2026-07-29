# Preguntas frecuentes

## ¿AI Processing contabiliza o paga?

No. Prepara evidencia y datos para un borrador. La publicación y el pago siguen
siendo acciones normales de Odoo.

## ¿Puede usar un servidor propio?

Sí. Puede configurar una API OpenAI-compatible o un servidor Ollama, incluida
una URL interna autorizada.

## ¿Necesita clave un servidor local?

No necesariamente. El módulo admite una clave vacía para Ollama o un servidor
compatible propio. Se recomienda autenticación en entornos de producción.

## ¿Puede leer PDF escaneados?

Sí, si el modelo acepta visión. Para Ollama y servidores compatibles las
páginas se renderizan como imágenes.

## ¿Qué sucede con varios adjuntos?

Cada archivo es un trabajo independiente. Un fallo no cancela los demás.

## ¿Qué sucede con GIF o firmas?

Se conservan con una explicación, pero no se envían al modelo.

## ¿El cuerpo del correo controla la IA?

No. No forma parte de las instrucciones del modelo.

## ¿Qué cuenta de correo debe usarse?

Para recibir, se recomienda un buzón compartido y dedicado, como
`facturas@empresa.com`, conectado a Odoo por IMAP. Para enviar, sirve cualquier
cuenta cuyo dominio esté permitido. El módulo no necesita SMTP saliente para
procesar facturas. Consulte [Elegir y conectar el correo](../administracion/correo.md).

## ¿Puede crear un proveedor que falta?

No. Debe existir un proveedor con NIF/VAT exacto.

## ¿Selecciona impuestos y cuentas?

No. Los datos fiscales extraídos son evidencia para la revisión.

## ¿Cuándo se usa el respaldo?

Ante un fallo temporal, un rechazo específico del modelo o una salida
estructurada inválida. No se usa ante claves erróneas o bloqueos de seguridad.

## ¿Por qué un modelo no es seleccionable?

Debe estar disponible y tener capacidad documental declarada, verificada o
aprobada.

## ¿Cómo detecta duplicados?

Primero por la huella del archivo dentro de la empresa y después, cuando es
posible, por proveedor y referencia.

## ¿Es multiempresa?

Sí. Configuración, bandeja, documentos, modelos e intentos están separados por
empresa.

## ¿La lista de dominios autentica el correo?

No. Es un filtro de entrada. SPF, DKIM y DMARC deben aplicarse en la pasarela.

## ¿Qué versiones de Odoo admite?

Odoo 19 Community es el objetivo probado. Consulte
[Compatibilidad](../COMPATIBILITY.md) para otros entornos.
