# Elegir y conectar el correo

AI Processing recibe facturas mediante el sistema de correo entrante de Odoo.
No utiliza una cuenta SMTP para procesarlas.

## Qué dirección debe elegir

Para una instalación propia de Odoo, la opción más sencilla es crear un buzón
compartido y dedicado:

```text
facturas@empresa.com
```

Evite conectar el correo personal de una persona. Un buzón funcional permanece
estable cuando cambia el equipo, separa las facturas del resto de mensajes y
permite aplicar permisos y retención específicos.

No confunda estas direcciones:

| Elemento | Para qué sirve | Ejemplo |
|---|---|---|
| Cuenta remitente | Dirección desde la que una persona o proveedor envía la factura | `administracion@proveedor.com` |
| Buzón receptor | Cuenta compartida que Odoo consulta | `facturas@empresa.com` |
| Alias de AI Processing | Dirección de enrutamiento creada por el módulo para una empresa | `ai-invoices-1@correo.empresa.com` |
| Servidor saliente | SMTP usado por Odoo para enviar mensajes | No es necesario para recibir facturas |

AI Processing no obliga a usar una cuenta remitente concreta. Acepta las
direcciones cuyos dominios estén autorizados en **Correo y seguridad**. Si debe
permitirse una única dirección y no todo su dominio, aplique esa regla en el
proveedor de correo o en la pasarela anterior a Odoo.

## Opción recomendada: buzón compartido por IMAP

Este recorrido es el recomendado para Odoo 19 instalado en un servidor propio.
Odoo indica que los servidores entrantes están pensados para buzones
compartidos y recomienda IMAP frente a POP.

### 1. Cree el buzón

Cree `facturas@empresa.com` en su proveedor habitual de correo. Puede ser un
buzón nuevo o uno compartido, pero debe disponer de acceso IMAP u OAuth.

Anote sin publicar:

- servidor IMAP;
- puerto, normalmente `993`;
- uso de SSL/TLS;
- usuario;
- contraseña de aplicación o autorización OAuth.

No guarde estas credenciales en Git, documentación, mensajes de soporte ni
campos de configuración de AI Processing.

### 2. Conéctelo a Odoo

Active el modo de desarrollador y abra:

```text
Ajustes → Técnico → Correos electrónicos → Servidores de correo entrante
```

Cree un servidor con estos criterios:

| Campo de Odoo | Valor |
|---|---|
| Nombre | `Facturas de proveedor` |
| Tipo de servidor | `IMAP` |
| Servidor y puerto | Los indicados por el proveedor |
| SSL/TLS | Activado cuando use IMAPS, normalmente en el puerto 993 |
| Usuario y credencial | Los del buzón compartido |
| Crear un nuevo registro | `AI Processing incoming email` (`ai.processing.inbox`) |
| Conservar adjuntos | Activado |
| Conservar original | Opcional; duplica aproximadamente el almacenamiento del mensaje |

Si están instalados los conectores correspondientes de Odoo, Gmail y Microsoft
365 también pueden autorizarse mediante OAuth.

Pulse **Probar y confirmar**. Cuando la conexión sea válida, use **Recibir
ahora** para la primera prueba. Después Odoo consultará el buzón mediante su
acción programada de correo entrante.

### 3. Termine la configuración en AI Processing

Abra:

```text
Contabilidad → AI Processing → Configuración → Correo y seguridad
```

1. Añada inicialmente solo su propio dominio a **Dominios remitentes
   permitidos**.
2. Mantenga un caudal bajo durante la prueba.
3. Guarde la configuración.
4. Envíe una factura conocida a `facturas@empresa.com`.
5. Compruebe el correo, sus adjuntos y el borrador creado en Odoo.

En este recorrido la dirección pública es el buzón compartido. El alias que
muestra AI Processing sigue identificando el enrutamiento interno del módulo,
pero no es necesario publicarlo a proveedores.

## Alternativa: reenviar al alias de AI Processing

También puede usar una dirección amigable, como `facturas@empresa.com`, que
redirija los mensajes al alias completo mostrado por AI Processing.

Esta opción es útil cuando una pasarela ya entrega correo a los alias de Odoo.
En instalaciones propias, la redirección directa y el método por registro MX
requieren configurar la puerta de enlace técnica de Odoo. No publique el alias
hasta que una prueba confirme que se conserva el destinatario y que Odoo lo
enruta a la empresa correcta.

Para varias empresas, mantenga un alias y una ruta de correo independientes por
empresa. No use un único buzón sin comprobar explícitamente a qué empresa se
asignará cada mensaje.

## Dominios remitentes permitidos

Introduzca un dominio por línea o sepárelos con coma o punto y coma:

```text
empresa.com
proveedor.example
asesoria.example
```

Se acepta el dominio exacto y sus subdominios. `facturas.proveedor.example`
coincide con `proveedor.example`; `falso-proveedor.example` no coincide.

Si la lista queda vacía, cualquier remitente encaminado por Odoo puede crear un
registro. Esta opción no se recomienda para un buzón expuesto a Internet.

La lista no autentica al remitente. SPF, DKIM, DMARC, antimalware y las reglas
de rechazo deben ejecutarse antes de que Odoo acepte el mensaje.

## Caudal y adjuntos

El límite de correos por minuto se aplica por empresa. Los documentos que
superan temporalmente el caudal permanecen en cola.

El límite de adjuntos se refiere a archivos elegibles por mensaje. Los adjuntos
adicionales se conservan sin enviarse al modelo.

## Prueba de extremo a extremo

1. Envíe una factura conocida desde un dominio autorizado.
2. Pulse **Recibir ahora** durante la primera prueba o espere la recogida
   programada.
3. Compruebe la recepción en **Bandeja de facturas**.
4. Confirme remitente, destinatario, asunto e identificador del mensaje.
5. Verifique que todos los adjuntos aparecen.
6. Compruebe qué archivos son candidatos, ignorados o duplicados.
7. Procese un candidato, abra el borrador y revise su historial.
8. Confirme que la factura continúa sin contabilizar.

Una prueba directa de la API del proveedor de IA no valida el correo entrante.

## Si el correo no aparece

Revise, en este orden:

1. que **Probar y confirmar** funciona;
2. que el buzón contiene el mensaje como no leído;
3. que **Conservar adjuntos** está activado;
4. que el modelo seleccionado es `AI Processing incoming email`;
5. que el dominio del remitente está permitido;
6. que la acción programada de correo entrante está activa;
7. que el mensaje no fue rechazado por SPF, DKIM, DMARC o antimalware.

Consulte también [Solución de problemas](../operaciones/solucion-de-problemas.md).

## Documentación oficial de Odoo 19

- [Gestionar mensajes entrantes](https://www.odoo.com/documentation/19.0/es/applications/general/email_communication/email_servers_inbound.html)
- [Comunicación por correo electrónico](https://www.odoo.com/documentation/19.0/applications/general/email_communication.html)
- [Problemas habituales del correo](https://www.odoo.com/documentation/19.0/applications/general/email_communication/faq.html)
