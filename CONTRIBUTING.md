# Contribuir

Gracias por mejorar AI Processing.

## Antes de abrir un cambio

1. Describe el problema desde el punto de vista del usuario.
2. No incluyas facturas reales, datos personales ni claves.
3. Mantén separadas la extracción de datos y la autoridad contable.
4. Añade o actualiza pruebas cuando cambie el comportamiento.
5. Documenta los cambios visibles en `CHANGELOG.md`.

## Comprobaciones

```bash
python3 -m pip install -r requirements-audit.txt
ruff check .
python3 -m unittest discover -s tests_unit -v
mkdocs build --strict
```

Para los cambios que dependan de Odoo:

```bash
docker compose -f compose.test.yaml up --build --renew-anon-volumes \
  --abort-on-container-exit --exit-code-from odoo-test
```

## Pull requests

Explica qué cambia, por qué, cómo lo verá la persona usuaria y qué pruebas has
ejecutado. Evita mezclar cambios de producto, refactorizaciones y ajustes de
formato que no estén relacionados.
