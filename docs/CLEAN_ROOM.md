# Clean-room development record

## Inputs allowed for the core implementation

- `AI Processing — Especificación funcional clean-room`, version 1.0;
- official Odoo 19 documentation and official Odoo 19 container image;
- official provider API documentation;
- authorized invoice fixtures and acceptance results;
- generally available Python library documentation.

## Inputs excluded

- the original third-party invoice addon ZIP;
- the previously adapted addon source;
- the restricted migration field map;
- code, tests, prompts, XML IDs and internal naming from either comparison base.

## Repository boundary

This repository was initialized empty and has its own Git history. The legacy
migration adapter is intentionally absent. It may be developed later in a
separate package after the public schema of this addon is frozen.

## Engineering verification

- exact-line, token and structural similarity report;
- unit and Odoo integration tests;
- security review;
- authorship/access log;

The current automated result is recorded in
[`INDEPENDENCE_AUDIT.md`](INDEPENDENCE_AUDIT.md).
The authorship record is in [`PROVENANCE.md`](PROVENANCE.md).

An SPDX SBOM and legal review remain prerequisites for a production release and
for any claim of exclusive legal ownership.
