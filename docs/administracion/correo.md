# Correo entrante

AI Processing utiliza el sistema de alias y correo entrante de Odoo.

## Requisitos

- un dominio de alias configurado;
- una pasarela que entregue mensajes a Odoo;
- un alias de AI Processing por empresa;
- permisos y reglas de correo coherentes;
- validación SPF, DKIM y DMARC en la pasarela.

## Lista de dominios permitidos

Introduzca un dominio por línea o sepárelos con coma o punto y coma:

```text
proveedor.example
asesoria.example
```

Se acepta el dominio exacto y sus subdominios. `facturas.proveedor.example`
coincide con `proveedor.example`; `falso-proveedor.example` no coincide.

Si la lista queda vacía, cualquier remitente encaminado por Odoo puede crear un
registro. Esta opción no se recomienda para un alias expuesto a Internet.

La lista no autentica al remitente. El filtrado criptográfico y la política de
rechazo deben ejecutarse antes de que Odoo acepte el mensaje.

## Caudal

El límite de correos por minuto se aplica por empresa. Los documentos que
superan temporalmente el caudal permanecen en cola.

El límite de adjuntos se refiere a archivos elegibles por mensaje. Los adjuntos
adicionales se conservan sin enviarse al modelo.

## Prueba de extremo a extremo

1. Envíe desde un dominio autorizado.
2. Compruebe la recepción en Odoo.
3. Confirme remitente, destinatario, asunto e identificador del mensaje.
4. Verifique que todos los adjuntos aparecen.
5. Compruebe qué archivos son candidatos, ignorados o duplicados.
6. Procese un candidato y abra su historial.

Una prueba directa de la API del proveedor no valida el correo entrante.
