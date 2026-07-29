# Compatibility

## Odoo

| Platform | Status | Notes |
|---|---|---|
| Odoo 19 Community | Supported | Primary development and test target |
| Odoo 19 Enterprise | Expected | Uses Community APIs only; validate with installed Enterprise addons |
| Odoo.sh | Conditional | Python dependencies and incoming mail must be available |
| Odoo Online | Unsupported | Custom Python addons cannot normally be installed |
| Odoo 18 or older | Unsupported | Requires an explicit port and separate test matrix |

## AI services

| Service | Catalog | Document request | Status |
|---|---|---|---|
| Ollama local | `/api/tags` | `/api/chat`, rendered pages/images | Supported |
| Ollama Cloud | `/api/tags` | `/api/chat`, rendered pages/images | Supported |
| OpenAI | `/v1/models` | `/v1/responses`, native PDF/image | Supported, live credential test required |
| OpenRouter | `/api/v1/models` | `/api/v1/chat/completions` | Supported, model-dependent |
| OpenAI-compatible | `/v1/models` | `/v1/chat/completions`, images/rendered PDF | Supported when required features exist |

Compatibility is capability-based. A reachable model is not necessarily able
to read documents or return strict structured data.

## File types

- PDF;
- JPEG;
- PNG;
- WebP.

GIF and all other formats are preserved but not processed.

## Python dependencies

- `requests`;
- `Pillow`;
- `pypdf`;
- `pypdfium2`;
- `cryptography`.

All are runtime dependencies. Versions should be pinned and scanned in the
deployment image rather than vendored into the addon.
