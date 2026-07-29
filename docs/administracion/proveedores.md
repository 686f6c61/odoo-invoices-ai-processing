# Proveedores y servidores propios

Elija el protocolo por el contrato HTTP que ofrece el servidor, no solo por el
nombre comercial del modelo.

## OpenAI

- URL habitual: `https://api.openai.com/v1`
- Catálogo: `/models`
- Extracción: `/responses`
- Clave recomendada: `OPENAI_API_KEY`

El proveedor recibe PDF o imágenes mediante su entrada documental nativa.

## OpenRouter

- URL habitual: `https://openrouter.ai/api/v1`
- Catálogo: `/models`
- Extracción: `/chat/completions`
- Clave recomendada: `OPENROUTER_API_KEY`

La capacidad depende del modelo y del enrutamiento disponible. Revise también
el motor configurado para PDF.

## Ollama local o Cloud

- URL local habitual: `http://servidor:11434/api`
- URL Cloud habitual: `https://ollama.com/api`
- Catálogo: `/tags`
- Extracción: `/chat`
- Clave recomendada para Cloud: `OLLAMA_API_KEY`

Los PDF se convierten localmente en páginas visuales antes de llamar al modelo.
El límite de páginas visuales controla consumo y tiempo.

## Servidor OpenAI-compatible propio

El servidor debe ofrecer:

- `GET /v1/models`;
- `POST /v1/chat/completions`;
- entrada de imágenes mediante URL de datos;
- salida JSON que respete el contrato del módulo.

Seleccione **Servidor OpenAI-compatible** y escriba la URL base, por ejemplo:

```text
https://ia.empresa.example/v1
```

Para una red interna:

```text
http://10.20.0.15:8000/v1
```

En este segundo caso debe activar explícitamente el acceso a red privada.
Hágalo solo si la ruta, DNS, proxy y servidor pertenecen a su organización.

La clave puede quedar vacía si el servicio interno no exige autenticación. En
producción es preferible autenticar también los servicios internos.

## Servidor Ollama propio

Seleccione **Ollama local o Cloud** e indique la base `/api`. El servidor debe
ser accesible desde el contenedor o proceso de Odoo, no desde el navegador del
usuario.

En Docker, `localhost` apunta al propio contenedor de Odoo. Use el nombre del
servicio, una red interna o una dirección de host autorizada.

## Comprobación

Para cualquier proveedor:

1. Guarde URL y credencial.
2. Lea el catálogo.
3. Ejecute la sonda visual.
4. Seleccione el modelo.
5. Pruebe una factura sin datos especialmente sensibles.
6. Revise el historial y el borrador.

No apruebe manualmente un modelo que haya fallado la sonda sin investigar antes
el formato de entrada y la respuesta del servidor.
