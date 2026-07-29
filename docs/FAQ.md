# Frequently asked questions

## Does AI Processing post or pay invoices?

No. It prepares evidence and draft values. Posting and payment remain normal
Odoo accounting actions performed by an authorized user.

## Can it use my own server?

Yes. Select either the OpenAI-compatible or Ollama protocol, provide its base
URL and read the model catalog. API keys are optional for a local service. A
private URL must be explicitly allowed by an administrator.

## Does “OpenAI-compatible” mean only OpenAI models?

No. It describes the HTTP contract. Any server that implements the required
models and chat-completions endpoints and accepts image input can be used.

## Can it process scanned PDFs?

Yes, when the selected model accepts vision. PDF pages are rendered locally for
Ollama and generic chat-compatible servers. Native PDF input is used where the
provider supports it.

## Why is a model not selectable?

The server may not declare image/document input, the capability probe may not
have passed, or the model was unavailable in the latest catalog refresh. An
administrator can review the evidence and explicitly approve a model.

## What causes the fallback to run?

Temporary network/provider failure, a model-specific request rejection or a
response that fails the strict data contract. It does not hide authentication,
permission, consent, file or security errors.

## What happens to GIFs, signatures and unsupported files?

They remain attached to the email record with an explanation. They are not sent
to the model.

## What if one email contains several invoices?

Every accepted attachment is an independent work item. Each confirmed invoice
or credit note may create one draft; failure of one attachment does not cancel
the others.

## Does the email body instruct the model?

No. The body is not placed in the inference prompt. Attachments are explicitly
treated as untrusted data, including text that tries to give instructions.

## Which email account should be used?

For reception, use a dedicated shared mailbox such as
`invoices@company.example` and connect it to Odoo through IMAP. For sending,
any account whose domain is allowed can submit a document. Outgoing SMTP is not
required to process invoices. See
[Choosing and connecting email](administracion/correo.md).

## Can it create a missing supplier?

No. It only links a supplier by exact normalized VAT/NIF. Create or select the
supplier manually, then apply the reviewed result.

## Are taxes selected automatically?

No. Extracted tax rates and treatment are evidence and suggestions. Final
taxes, accounts and deductibility remain subject to accounting review.

## How are duplicates detected?

First by SHA-256 of the original file, scoped to the company. Supplier VAT plus
invoice number is a secondary control.

## Where is the API key stored?

Preferably only in the Odoo server environment. If pasted in the UI, it is
encrypted with a master key that remains outside the database.

## Why was a private endpoint blocked?

Public endpoints are the safe default. Loopback, private and link-local
addresses are rejected to prevent server-side request forgery. Enable private
access only for infrastructure you control.

## Can I retry a failed document?

Yes. A user with accounting rights can return a failed or “not an invoice”
document to the queue after correcting configuration or selecting another
model.

## Is the addon multi-company?

Yes. Configuration, inboxes, documents, models and attempts are isolated by
company through record rules and company checks.

## Is the sender-domain allowlist email authentication?

No. It is an intake filter after Odoo routes the message. Configure SPF, DKIM
and DMARC validation in the receiving mail service and reject or quarantine
failed authentication there.

## Which Odoo editions are supported?

Odoo 19 Community is the primary target. It uses only `account` and `mail`
features available in Community. See the compatibility matrix for other
versions and deployment types.
