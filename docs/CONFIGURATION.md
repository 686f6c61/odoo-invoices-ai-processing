# Configuration guide

## Start here

The configuration screen is deliberately ordered so that the normal setup does
not require opening advanced options.

### 1. Service

Choose the protocol spoken by the server:

| Choice | Expected API | Typical base URL |
|---|---|---|
| OpenAI | Responses API | `https://api.openai.com/v1` |
| OpenRouter | Chat Completions | `https://openrouter.ai/api/v1` |
| OpenAI-compatible server | Models + Chat Completions | `https://server.example/v1` |
| Ollama local or Cloud | Tags + Chat | `http://host:11434/api` or `https://ollama.com/api` |

The URL is editable in every case. Select the protocol by behavior, not by the
vendor's marketing name.

### 2. Secret

The recommended option is an environment variable in the Odoo process.
Defaults are `OPENAI_API_KEY`, `OPENROUTER_API_KEY` and `OLLAMA_API_KEY`.
Self-hosted services may leave the secret empty.

A pasted secret can only be saved when `AI_PROCESSING_MASTER_KEY` contains a
valid Fernet key in the server environment. It is encrypted before persistence
and never displayed again.

### 3. Read models

Click **Test connection and read models**. The addon keeps the historical
catalog, marks models missing from the latest response as unavailable and
records a safe result message.

Only models with declared, probed or manually approved document capability are
selectable. A model name alone is not durable evidence of vision support.

### 4. Select the chain

Choose a primary model. A different fallback is optional. The fallback is used
for temporary provider errors or invalid structured output, not for bad
credentials, blocked endpoints, unsupported documents or missing consent.

### 5. Incoming mail

For self-hosted Odoo, prefer a dedicated shared mailbox such as
`invoices@company.example`, connected through Odoo's incoming mail server with
IMAP and SSL/TLS. Select `AI Processing incoming email`
(`ai.processing.inbox`) as the model and keep attachments enabled. A personal
mailbox is not recommended.

An existing Odoo mail gateway may instead route messages to the per-company
alias created by AI Processing. The two delivery patterns should not be
confused: the shared mailbox is the public destination in the IMAP pattern,
while the module alias is the routing destination in the gateway pattern.

With an empty domain allowlist, any sender can reach the inbox. When domains are
listed, only exact domains and their subdomains are accepted after IDN
normalization. This is not sender authentication; enforce SPF, DKIM and DMARC
at the receiving mail service.

See [Choosing and connecting email](administracion/correo.md) for the complete
setup and end-to-end test.

### 6. Advanced controls

Keep temperature at zero for deterministic extraction. Increase output tokens
only for invoices with many commercial lines. Page, byte and time limits are
security and cost controls, not just performance settings.

Private endpoints bypass the default SSRF protection and must be enabled only
for a controlled internal server.

## Recommended initial values

- mode: manual;
- temperature: 0;
- output tokens: 4,000;
- API timeout: 90 seconds;
- document size: 12 MB;
- PDF pages: 20;
- visual PDF pages: 8;
- emails per minute: 5;
- processable attachments per email: 20;
- confidence warning threshold: 0.75.
