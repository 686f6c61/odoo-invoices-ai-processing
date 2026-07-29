# Changelog

Todos los cambios relevantes de AI Processing se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el módulo utiliza el esquema de versiones de Odoo.

## [19.0.1.0.1] - 2026-07-29

Primera distribución pública independiente.

### Añadido

- Recepción de correos con uno o varios adjuntos.
- Clasificación segura de PDF, JPEG, PNG, WebP, firmas, logotipos y duplicados.
- Extracción estructurada de proveedor, NIF/VAT, fechas, conceptos, importes,
  impuestos, moneda e IBAN.
- Proveedores OpenAI, OpenRouter, Ollama local o Cloud y servidores
  OpenAI-compatible.
- Catálogo de modelos con comprobación documental, modelo principal y respaldo.
- Cola persistente, reintentos, límites operativos e historial por documento.
- Borradores de facturas de proveedor sujetos a revisión humana.
- Configuración guiada, ayuda contextual y manual por perfiles.
- Landing responsive y guía de instalación.
- Pruebas unitarias, integración con Odoo 19 y validación de la documentación.

### Seguridad

- Validación local cerrada de los resultados.
- Protección contra duplicados, adjuntos modificados y destinatarios
  incompatibles.
- Bloqueo de direcciones privadas salvo autorización explícita.
- Claves desde variables de entorno o cifradas con una clave maestra externa.
- Ninguna publicación, pago o creación automática de proveedores.

[19.0.1.0.1]: https://github.com/686f6c61/odoo-invoices-ai-processing/releases/tag/v19.0.1.0.1
