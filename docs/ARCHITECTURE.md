# Architecture

AI Processing separates four layers:

1. `core`: provider-neutral schemas, validation, URL policy and HTTP adapters;
2. `configuration`: company profile, model catalog, secrets and capability
   evidence;
3. `intake`: email cases, preserved attachments and durable work queue;
4. `accounting`: staged evidence and explicit application to existing Odoo
   drafts.

Provider adapters do not import Odoo. Accounting code does not construct HTTP
requests. This makes the security-sensitive request and response contract
testable without an Odoo database.

## Data ownership

One company owns one profile. The profile owns its model catalog and email
alias. An email case owns document records; the underlying `ir.attachment`
remains the source file. A document may link to at most one draft. Every model
attempt is immutable and links back to the document and optional draft.

## Queue

Workers reserve pending documents atomically. A database advisory lock keyed by
company and file hash closes the final duplicate race. Processing occurs inside
a savepoint per document. Stale reservations return to pending state.

## Result lifecycle

The provider response is validated into a closed contract, normalized and
checked. It is then staged as evidence. Only a separate user action maps safe
fields and commercial lines into a draft.
