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

Para una instalación propia, cree preferentemente un buzón compartido y
dedicado, como `facturas@empresa.com`, y conéctelo a Odoo mediante IMAP. No use
el correo personal de una persona ni confunda el buzón receptor con el alias
interno que muestra el módulo.

En **Correo y seguridad**:

- añada dominios permitidos;
- establezca correos por minuto;
- establezca adjuntos procesables por mensaje.

Siga [Elegir y conectar el correo](correo.md) para configurar el buzón, el
servidor entrante, el modelo de destino y la prueba completa.

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
