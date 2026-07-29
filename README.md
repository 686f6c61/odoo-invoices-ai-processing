# Odoo Invoices · AI Processing

AI Processing es un módulo independiente para **Odoo 19 Community** que
convierte los adjuntos de facturas de proveedor en borradores listos para
revisión.

Recibe varios archivos por correo, separa facturas de firmas y logotipos,
extrae proveedor, conceptos e importes y conserva la decisión final en manos
del equipo contable.

- **Producto y demostración:** <https://ai-processing.686f6c61.dev/>
- **Guía de instalación:** <https://ai-processing.686f6c61.dev/instalar.html>
- **Manual completo:** [docs/index.md](docs/index.md)
- **Última versión:** `19.0.1.0.1`
- **Licencia:** LGPL-3.0

## Qué resuelve

- Procesa uno o varios adjuntos por correo.
- Acepta PDF, JPEG, PNG y WebP; conserva y descarta con motivo los archivos no
  adecuados.
- Detecta duplicados antes de volver a procesar un documento.
- Extrae proveedor, NIF/VAT, fechas, conceptos, importes, impuestos, moneda e
  IBAN.
- Funciona con OpenAI, OpenRouter, Ollama local o Cloud y servidores propios
  compatibles.
- Permite elegir un modelo principal y otro de respaldo.
- Crea únicamente borradores revisables: nunca publica, paga o crea proveedores
  automáticamente.
- Mantiene historial de intentos, estados y alertas por documento.

## Compatibilidad

| Componente | Compatibilidad |
|---|---|
| Odoo | 19.0 Community |
| Aplicaciones Odoo | Contabilidad y Correo |
| OpenAI | Responses API |
| OpenRouter | Chat Completions |
| Ollama | Local y Cloud |
| Servidor propio | API OpenAI-compatible |
| Licencia | LGPL-3.0 |

La matriz detallada y las limitaciones conocidas están en
[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## Instalación

### Opción recomendada: release

1. Descarga `ai_processing-19.0.1.0.1.zip` desde la
   [última release](https://github.com/686f6c61/odoo-invoices-ai-processing/releases/latest).
2. Descomprime la carpeta `ai_processing` dentro de una ruta de addons de Odoo.
3. Instala las dependencias Python en el mismo entorno que ejecuta Odoo:

   ```bash
   python3 -m pip install requests pypdf pypdfium2 cryptography
   ```

4. Reinicia Odoo y actualiza la lista de aplicaciones.
5. Busca **AI Processing** y pulsa **Activar**.

### Desde el repositorio

```bash
git clone https://github.com/686f6c61/odoo-invoices-ai-processing.git
```

Copia `ai_processing/` a tu ruta de addons o añade el repositorio a
`addons_path`. No copies `.env`, claves, bases de datos ni archivos de
producción.

## Primera configuración

1. Abre **Contabilidad → AI Processing → Configuración**.
2. Elige OpenAI, OpenRouter, Ollama o un servidor propio.
3. Indica el nombre de la variable de entorno que contiene la clave.
4. Pulsa **Probar conexión y leer modelos**.
5. Selecciona un modelo documental principal y un respaldo.
6. Define dominios aceptados, límites de correo y consentimiento.
7. Conecta preferentemente un buzón compartido por IMAP al modelo
   `ai.processing.inbox`.
8. Guarda y envía una factura conocida al buzón o alias configurado.

> En el campo de variable escribe `OLLAMA_API_KEY`, `OPENAI_API_KEY` o
> `OPENROUTER_API_KEY`; no pegues ahí el valor real de la clave. Si necesitas
> guardar una clave cifrada en Odoo, configura `AI_PROCESSING_MASTER_KEY` fuera
> de la base de datos y de Git.

La guía visual completa está en
[landing/instalar.html](landing/instalar.html) y en
[docs/administracion/configuracion-inicial.md](docs/administracion/configuracion-inicial.md).
La elección del buzón y su conexión a Odoo están documentadas en
[docs/administracion/correo.md](docs/administracion/correo.md).

## Seguridad contable

El modelo propone; Odoo y la persona responsable deciden:

- no publica asientos;
- no ordena pagos;
- no crea proveedores, cuentas bancarias, impuestos ni cuentas contables;
- vincula proveedores únicamente mediante coincidencia exacta;
- bloquea adjuntos alterados, duplicados y destinatarios incompatibles;
- limita tamaño, páginas, líneas, tiempo y respuesta;
- mantiene las claves fuera del repositorio;
- exige una acción humana antes de aplicar los valores al borrador.

Consulta [docs/SECURITY.md](docs/SECURITY.md) y
[SECURITY.md](SECURITY.md) antes de exponer un servidor propio o aceptar correo
externo.

## Documentación

El manual está organizado por perfiles:

- [Primeros pasos](docs/usuarios/primeros-pasos.md)
- [Enviar facturas](docs/usuarios/enviar-facturas.md)
- [Revisar resultados](docs/usuarios/revisar-resultados.md)
- [Configuración inicial](docs/administracion/configuracion-inicial.md)
- [Proveedores de IA](docs/administracion/proveedores.md)
- [Elegir y conectar el correo](docs/administracion/correo.md)
- [Copias y actualizaciones](docs/operaciones/copias-y-actualizaciones.md)
- [Solución de problemas](docs/operaciones/solucion-de-problemas.md)
- [Preguntas frecuentes](docs/referencia/faq.md)

Para servir la wiki en local:

```bash
python3 -m pip install -r requirements-docs.txt
mkdocs serve
```

## Desarrollo y validación

Las pruebas puras no necesitan Odoo:

```bash
python3 -m pip install -r requirements-ci.txt
ruff check .
python3 -m unittest discover -s tests_unit -v
mkdocs build --strict
```

La integración completa utiliza una base efímera y Odoo 19:

```bash
docker compose -f compose.test.yaml build
docker compose -f compose.test.yaml down -v
docker compose -f compose.test.yaml up --renew-anon-volumes \
  --abort-on-container-exit --exit-code-from odoo-test
```

La landing se sirve desde el `Dockerfile` raíz. El contenedor de pruebas de
Odoo utiliza `Dockerfile.odoo`.

## Versionado y cambios

El módulo sigue el versionado habitual de Odoo:
`19.0.<major>.<minor>.<patch>`.

Los cambios de cada entrega están en [CHANGELOG.md](CHANGELOG.md). Las releases
incluyen un ZIP instalable y su checksum SHA-256.

## Independencia y procedencia

La implementación fue desarrollada de forma independiente. Los límites del
trabajo limpio, la auditoría de independencia, las entradas permitidas y los
avisos de terceros están documentados en:

- [docs/CLEAN_ROOM.md](docs/CLEAN_ROOM.md)
- [docs/INDEPENDENCE_AUDIT.md](docs/INDEPENDENCE_AUDIT.md)
- [docs/PROVENANCE.md](docs/PROVENANCE.md)
- [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md)

Copyright © 2026 00B.
