# Provenance

## Development record

- The repository was initialized as an empty, independent codebase on
  2026-07-29.
- The implementation was derived from the functional requirements documented in
  this repository and from public Odoo and provider API contracts.
- The legacy add-on was used to understand the requested business problem. Its
  source files were not copied into this repository.
- Automated source-similarity checks were performed only after the independent
  implementation was complete. Their results are recorded in
  `INDEPENDENCE_AUDIT.md`.

## Inputs deliberately excluded

- Provider API keys and encryption master keys.
- Production configuration, database exports and email credentials.
- Real supplier invoices or extracted personal and financial data.
- Source files, images, translations and documentation from the legacy add-on.

## Verification evidence

The repository contains:

- pure-Python contract and provider tests;
- Odoo 19 installation and transaction tests;
- a pinned test container and dependency inventory;
- security, compatibility and clean-room documentation;
- continuous integration that runs without provider credentials.

This record supports engineering traceability. It is not a legal opinion about
copyright ownership or registrability.
