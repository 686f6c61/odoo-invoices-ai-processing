# Third-party notices

AI Processing is designed for Odoo 19 and uses its public addon APIs. Odoo and
the following Python packages are separate works with their own copyright and
license terms:

- Requests;
- Pillow;
- pypdf;
- pypdfium2;
- cryptography;
- pyOpenSSL.

`requirements-audit.txt` records the application dependency closure installed
in the pinned validation image. It overrides older distribution copies where
necessary.
Dependency updates are reviewed as one reproducible baseline rather than
through automated pull requests. The deployment owner must regenerate the
inventory, run a vulnerability scan and produce an SPDX inventory from the
exact production image whenever the base-image digest changes. This repository
does not vendor those packages.

AI provider services and models are not distributed by this addon. Their
commercial terms, privacy terms, retention and regional availability apply
independently.
