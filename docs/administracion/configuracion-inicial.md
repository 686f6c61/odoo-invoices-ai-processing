# Configuración inicial

La configuración se realiza por empresa en
**Contabilidad → AI Processing → Configuración**.

## 1. Servicio y clave

1. Seleccione el protocolo.
2. Revise la URL base completa.
3. Indique el nombre de la variable de entorno que contiene la clave.
4. Active acceso privado únicamente para un servidor interno controlado.
5. Guarde.

Se recomienda almacenar la clave como variable del proceso Odoo. Si se pega en
la interfaz, el servidor debe disponer de `AI_PROCESSING_MASTER_KEY`; la clave
se cifra y no vuelve a mostrarse.

## 2. Conexión y catálogo

Pulse **Probar conexión y leer modelos**. Debe aparecer el estado
**Conectado**, una fecha de sincronización y un mensaje seguro.

La lectura del catálogo no demuestra por sí sola que un modelo pueda leer
facturas. Abra **Modelos** y ejecute la sonda visual cuando sea necesario.

## 3. Cadena de modelos

Seleccione:

- un modelo principal apto para documentos;
- opcionalmente, otro modelo como respaldo.

El respaldo debe ser diferente del principal. Configure temperatura y tokens
en la ficha de cada modelo.

## 4. Consentimiento

Active **Permitir transferencia de documentos a este servicio** solo después de
comprobar proveedor, contrato, ubicación, retención y finalidad del tratamiento.
La autorización se comprueba antes de cada solicitud externa.

## 5. Correo

Compruebe que Odoo muestra un alias completo. Configure el dominio de alias y la
pasarela entrante si aparece **Dominio de alias no configurado**.

En **Correo y seguridad**:

- añada dominios permitidos;
- establezca correos por minuto;
- establezca adjuntos procesables por mensaje.

## 6. Activación

Empiece con modo **Manual** y una factura de prueba conocida. Pase a modo
automático solo después de validar proveedor, correo, modelos, límites y
procedimiento de revisión.

## Valores iniciales

| Parámetro | Valor orientativo |
|---|---:|
| Temperatura | 0 |
| Tokens de salida | 4.000 |
| Tiempo máximo | 90 s |
| Tamaño | 12 MB |
| Páginas PDF | 20 |
| Páginas visuales | 8 |
| Correos por minuto | 5 |
| Adjuntos por correo | 20 |
| Umbral de confianza | 0,75 |

Adapte los valores tras medir documentos reales; no los aumente para ocultar
errores de formato o de modelo.
