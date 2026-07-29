# Security model

## Trust boundaries

Incoming email, attachments, document text, provider responses, remote model
metadata and configurable endpoints are untrusted.

Odoo company identity, permissions, accounting state and administrator
configuration are trusted only after local validation.

## Controls

- binary signature checks and resource limits before inference;
- SHA-256 idempotency per company;
- strict response schema with no unknown properties;
- prompt-injection-resistant separation of instructions and document data;
- endpoint normalization and public-address enforcement by default;
- redirects disabled for provider calls;
- bounded response bodies and safe error messages;
- secrets from environment or encrypted at rest;
- company record rules and accounting group ACLs;
- atomic work reservation and stale-work recovery;
- explicit consent checked immediately before every external call;
- manual application to draft records only;
- exact VAT/NIF supplier matching;
- no automatic taxes, posting, payment or third-party creation.

## Operational requirements

- treat the public repository as code only and keep all operational data out;
- keep all provider and master keys outside Git;
- rotate any key pasted into chat, tickets or logs;
- enable a private endpoint only after verifying ownership and network route;
- enforce SPF, DKIM and DMARC at the incoming mail gateway;
- restrict Odoo system administration;
- keep database and filestore backups together and test restoration;
- review provider retention and regional processing terms;
- monitor queue age, failures, fallback use and unexpected cost;
- update the container and Python dependencies deliberately.

## Reporting

Do not open a public issue containing invoices, VAT numbers, API responses,
email addresses or secrets. Provide a redacted reproduction to the repository
owner through a private channel.
