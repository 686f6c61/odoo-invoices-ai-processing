# Estados y acciones

## Estados del correo

| Estado | Significado | Acción habitual |
|---|---|---|
| Recibido | Hay adjuntos aún sin enviar a la cola | Procesar candidatos si el modo es manual |
| Pendiente | Al menos un documento espera turno | Esperar o revisar la cola |
| Procesando | Un trabajador ha reservado un documento | Esperar; no reintentar |
| Revisión contable | Hay una factura detectada sin aplicar | Abrir y revisar el borrador |
| Completo | Los documentos ya no requieren trabajo | Archivar según el procedimiento interno |
| Parcialmente completo | Algunos adjuntos terminaron y otros fallaron | Revisar cada documento |
| Fallido | Todos los trabajos relevantes fallaron | Corregir la causa y reintentar |

## Estados del documento

| Estado | Significado |
|---|---|
| Candidato | Archivo válido pendiente de decisión manual |
| Pendiente | En cola |
| Procesando | Reservado por un trabajador |
| Factura detectada | Extracción validada y borrador disponible |
| No es factura | El modelo no lo clasificó como factura o abono |
| Ignorado | Formato, tamaño, límite o decisión manual impide procesarlo |
| Duplicado | Ya existe el mismo archivo en la empresa |
| Fallido | El intento terminó con un error seguro |

## Estados en el borrador

| Estado | Significado |
|---|---|
| Sin analizar | Todavía no se ha solicitado extracción |
| Pendiente / Analizando | El trabajo está en curso |
| Listo para revisión | Resultado sin alertas locales |
| Revisión requerida | Hay alertas o confianza baja |
| Fallido | No se obtuvo un resultado válido |
| Aplicado al borrador | Los campos permitidos se copiaron |

## Acciones

- **Procesar candidatos**: envía los adjuntos elegibles a la cola.
- **Procesar o reintentar**: repite un documento fallido o no clasificado.
- **Ignorar**: cierra manualmente un documento que no debe procesarse.
- **Analizar documento**: analiza el adjunto principal de un borrador.
- **Aplicar al borrador**: copia la extracción validada al borrador.
- **Abrir borrador**: abre el asiento relacionado sin contabilizarlo.
