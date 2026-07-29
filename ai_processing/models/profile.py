import os
import re
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from markupsafe import Markup
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..core import EndpointPolicyError, ProviderError, ProviderGateway, ProviderSettings

MASTER_KEY_ENV = "AI_PROCESSING_MASTER_KEY"
DOMAIN_SEPARATOR = re.compile(r"[\s,;]+")


class AIProcessingProfile(models.Model):
    _name = "ai.processing.profile"
    _inherit = ["mail.alias.mixin"]
    _description = "AI Processing company profile"
    _rec_name = "company_id"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        ondelete="cascade",
        index=True,
    )
    mode = fields.Selection(
        [
            ("off", "Disabled"),
            ("manual", "Manual review"),
            ("automatic", "Analyze incoming documents automatically"),
        ],
        default="manual",
        required=True,
    )
    protocol = fields.Selection(
        [
            ("ollama", "Ollama local or Cloud"),
            ("openai", "OpenAI"),
            ("openrouter", "OpenRouter"),
            ("openai_compatible", "OpenAI-compatible server"),
        ],
        default="ollama",
        required=True,
    )
    base_url = fields.Char(
        required=True,
        default="https://ollama.com/api",
        help="Full API base URL, including /api or /v1 when required.",
    )
    api_key_env = fields.Char(
        string="Secret environment variable",
        default="OLLAMA_API_KEY",
    )
    api_key_ciphertext = fields.Text(
        groups="base.group_system",
        copy=False,
    )
    api_key_input = fields.Char(
        string="Paste a new API key",
        compute="_compute_api_key_input",
        inverse="_inverse_api_key_input",
        store=False,
        groups="base.group_system",
    )
    credential_state = fields.Selection(
        [
            ("environment", "Available from server environment"),
            ("encrypted", "Stored encrypted"),
            ("not_required", "Not required by this local server"),
            ("missing", "Missing"),
        ],
        compute="_compute_credential_status",
    )
    master_key_ready = fields.Boolean(compute="_compute_credential_status")
    transfer_consent = fields.Boolean(
        string="Allow document transfer to this service",
        help="Required immediately before every external request.",
    )
    allow_private_endpoint = fields.Boolean(
        string="Allow private network endpoint",
        help="Enable only for an internal service controlled by your organization.",
    )
    structured_mode = fields.Selection(
        [("schema", "Strict JSON Schema"), ("json", "JSON with local validation")],
        default="json",
        required=True,
    )
    pdf_engine = fields.Selection(
        [
            ("auto", "Automatic"),
            ("native", "Native model processing"),
            ("cloudflare-ai", "Cloudflare AI"),
            ("mistral-ocr", "Mistral OCR (may add cost)"),
        ],
        default="auto",
        required=True,
    )
    pdf_detail = fields.Selection(
        [("auto", "Automatic"), ("low", "Low token use"), ("high", "High detail")],
        default="auto",
        required=True,
    )
    timeout_seconds = fields.Integer(default=90, required=True)
    max_document_mb = fields.Integer(default=12, required=True)
    max_pdf_pages = fields.Integer(default=20, required=True)
    max_visual_pages = fields.Integer(default=8, required=True)
    emails_per_minute = fields.Integer(default=5, required=True)
    attachments_per_email = fields.Integer(default=20, required=True)
    confidence_threshold = fields.Float(default=0.75, required=True)
    allowed_sender_domains = fields.Text(
        help="Comma or line-separated domains. Exact domains and subdomains are accepted."
    )
    company_guidance = fields.Text(
        help="Trusted extraction guidance. It cannot disable accounting safeguards."
    )
    model_ids = fields.One2many(
        "ai.processing.engine.model",
        "profile_id",
        string="Model catalog",
    )
    primary_model_id = fields.Many2one(
        "ai.processing.engine.model",
        check_company=True,
        ondelete="restrict",
        domain="[('profile_id', '=', id), ('protocol', '=', protocol), ('available', '=', True), ('document_capable', '=', True)]",
    )
    fallback_model_id = fields.Many2one(
        "ai.processing.engine.model",
        check_company=True,
        ondelete="restrict",
        domain="[('profile_id', '=', id), ('protocol', '=', protocol), ('available', '=', True), ('document_capable', '=', True)]",
    )
    connection_state = fields.Selection(
        [
            ("not_tested", "Not tested"),
            ("ok", "Connected"),
            ("error", "Connection error"),
        ],
        default="not_tested",
        required=True,
        readonly=True,
    )
    last_catalog_sync = fields.Datetime(readonly=True)
    last_connection_message = fields.Char(readonly=True)
    setup_step = fields.Selection(
        [
            ("service", "1 · Service"),
            ("models", "2 · Read models"),
            ("selection", "3 · Select models"),
            ("consent", "4 · Consent"),
            ("ready", "Ready"),
        ],
        compute="_compute_setup",
    )
    setup_ready = fields.Boolean(compute="_compute_setup")
    alias_address = fields.Char(compute="_compute_alias_address")
    processed_count = fields.Integer(compute="_compute_metrics")
    pending_count = fields.Integer(compute="_compute_metrics")
    failed_count = fields.Integer(compute="_compute_metrics")
    fallback_success_count = fields.Integer(compute="_compute_metrics")
    guide_html = fields.Html(compute="_compute_help", sanitize=False)
    faq_html = fields.Html(compute="_compute_help", sanitize=False)

    _company_unique = models.Constraint(
        "unique(company_id)",
        "Only one AI Processing profile is allowed per company.",
    )

    @api.model_create_multi
    def create(self, values_list):
        company_ids = [
            values.get("company_id") or self.env.company.id
            for values in values_list
        ]
        if len(company_ids) != len(set(company_ids)) or self.search_count(
            [("company_id", "in", company_ids)]
        ):
            raise ValidationError(
                _("Only one AI Processing profile is allowed per company.")
            )
        inbox_model_id = self.env["ir.model"]._get_id("ai.processing.inbox")
        if not inbox_model_id:
            raise UserError(_("The AI Processing inbox model is unavailable."))
        prepared = []
        for values in values_list:
            item = dict(values)
            company = self.env["res.company"].browse(
                item.get("company_id") or self.env.company.id
            )
            item.setdefault("alias_model_id", inbox_model_id)
            item.setdefault("alias_contact", "everyone")
            item.setdefault("alias_defaults", repr({"company_id": company.id}))
            prepared.append(item)
        return super().create(prepared)

    @api.onchange("protocol")
    def _onchange_protocol(self):
        defaults = {
            "ollama": ("https://ollama.com/api", "OLLAMA_API_KEY", "json"),
            "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "schema"),
            "openrouter": (
                "https://openrouter.ai/api/v1",
                "OPENROUTER_API_KEY",
                "schema",
            ),
            "openai_compatible": ("https://server.example/v1", "", "schema"),
        }
        self.base_url, self.api_key_env, self.structured_mode = defaults[self.protocol]
        self.primary_model_id = False
        self.fallback_model_id = False
        self.connection_state = "not_tested"

    @api.constrains(
        "timeout_seconds",
        "max_document_mb",
        "max_pdf_pages",
        "max_visual_pages",
        "emails_per_minute",
        "attachments_per_email",
        "confidence_threshold",
    )
    def _check_limits(self):
        for profile in self:
            ranges = [
                (
                    10 <= profile.timeout_seconds <= 300,
                    _("Timeout must be between 10 and 300 seconds."),
                ),
                (
                    1 <= profile.max_document_mb <= 40,
                    _("Document size must be between 1 and 40 MB."),
                ),
                (
                    1 <= profile.max_pdf_pages <= 50,
                    _("PDF pages must be between 1 and 50."),
                ),
                (
                    1 <= profile.max_visual_pages <= 12,
                    _("Visual PDF pages must be between 1 and 12."),
                ),
                (
                    1 <= profile.emails_per_minute <= 60,
                    _("Emails per minute must be between 1 and 60."),
                ),
                (
                    1 <= profile.attachments_per_email <= 100,
                    _("Attachments per email must be between 1 and 100."),
                ),
                (
                    0 <= profile.confidence_threshold <= 1,
                    _("Confidence threshold must be between 0 and 1."),
                ),
            ]
            for valid, message in ranges:
                if not valid:
                    raise ValidationError(message)

    @api.constrains("primary_model_id", "fallback_model_id", "protocol")
    def _check_model_chain(self):
        for profile in self:
            if (
                profile.primary_model_id
                and profile.primary_model_id == profile.fallback_model_id
            ):
                raise ValidationError(
                    _("Primary and fallback models must be different.")
                )
            for selected in (profile.primary_model_id, profile.fallback_model_id):
                if selected and (
                    selected.profile_id != profile
                    or selected.protocol != profile.protocol
                    or not selected.available
                    or not selected.document_capable
                ):
                    raise ValidationError(
                        _(
                            "Selected models must be available and verified for documents."
                        )
                    )

    @api.constrains("base_url")
    def _check_base_url(self):
        for profile in self:
            if profile.base_url:
                try:
                    from ..core.providers import normalize_base_url

                    normalize_base_url(profile.base_url)
                except EndpointPolicyError as error:
                    raise ValidationError(str(error)) from error

    @api.constrains("allowed_sender_domains")
    def _check_domains(self):
        for profile in self:
            profile.normalized_sender_domains()

    def normalized_sender_domains(self):
        self.ensure_one()
        result = []
        for candidate in DOMAIN_SEPARATOR.split(self.allowed_sender_domains or ""):
            value = candidate.strip().lower().lstrip("@").rstrip(".")
            if not value:
                continue
            try:
                value = value.encode("idna").decode("ascii")
            except UnicodeError as error:
                raise ValidationError(
                    _("Invalid sender domain: %s", candidate)
                ) from error
            labels = value.split(".")
            if (
                "." not in value
                or len(value) > 253
                or any(
                    not label
                    or len(label) > 63
                    or label.startswith("-")
                    or label.endswith("-")
                    or not re.fullmatch(r"[a-z0-9-]+", label)
                    for label in labels
                )
            ):
                raise ValidationError(_("Invalid sender domain: %s", candidate))
            if value not in result:
                result.append(value)
        return result

    def _compute_api_key_input(self):
        for profile in self:
            profile.api_key_input = False

    def _inverse_api_key_input(self):
        for profile in self:
            if profile.api_key_input:
                profile._store_api_key(profile.api_key_input)
                profile.api_key_input = False

    def _master_key(self):
        value = os.environ.get(MASTER_KEY_ENV, "").strip()
        if not value:
            return None
        try:
            return Fernet(value.encode())
        except (TypeError, ValueError):
            return None

    def _store_api_key(self, value):
        self.ensure_one()
        secret = (value or "").strip()
        if not secret:
            return
        cipher = self._master_key()
        if not cipher:
            raise UserError(
                _(
                    "The server must define a valid %s before pasted keys can be saved.",
                    MASTER_KEY_ENV,
                )
            )
        self.sudo().api_key_ciphertext = cipher.encrypt(secret.encode()).decode()

    def _runtime_api_key(self):
        self.ensure_one()
        env_name = (self.api_key_env or "").strip()
        if env_name and not re.fullmatch(r"[A-Z_][A-Z0-9_]*", env_name):
            raise UserError(_("The secret environment variable name is invalid."))
        if env_name and os.environ.get(env_name):
            return os.environ[env_name].strip()
        if not self.api_key_ciphertext:
            return ""
        cipher = self._master_key()
        if not cipher:
            raise UserError(
                _(
                    "The encrypted API key cannot be opened because the master key is unavailable."
                )
            )
        try:
            return cipher.decrypt(self.api_key_ciphertext.encode()).decode()
        except InvalidToken as error:
            raise UserError(
                _("The encrypted API key cannot be opened with the current master key.")
            ) from error

    @api.depends("api_key_env", "api_key_ciphertext", "base_url", "protocol")
    def _compute_credential_status(self):
        for profile in self:
            profile.master_key_ready = bool(profile._master_key())
            env_name = (profile.api_key_env or "").strip()
            if env_name and os.environ.get(env_name):
                profile.credential_state = "environment"
            elif profile.api_key_ciphertext:
                profile.credential_state = "encrypted"
            elif profile._key_optional():
                profile.credential_state = "not_required"
            else:
                profile.credential_state = "missing"

    def _key_optional(self):
        self.ensure_one()
        host = (urlsplit(self.base_url or "").hostname or "").lower()
        return self.protocol in {"ollama", "openai_compatible"} and host not in {
            "ollama.com",
            "api.openai.com",
            "openrouter.ai",
        }

    @api.depends(
        "connection_state",
        "primary_model_id",
        "primary_model_id.document_capable",
        "primary_model_id.available",
        "transfer_consent",
        "credential_state",
    )
    def _compute_setup(self):
        for profile in self:
            if profile.credential_state == "missing":
                step = "service"
            elif profile.connection_state != "ok":
                step = "models"
            elif not profile.primary_model_id:
                step = "selection"
            elif not profile.transfer_consent:
                step = "consent"
            else:
                step = "ready"
            profile.setup_step = step
            profile.setup_ready = step == "ready"

    @api.depends("alias_id", "alias_name", "alias_domain_id")
    def _compute_alias_address(self):
        for profile in self:
            domain = profile.alias_domain_id.name if profile.alias_domain_id else ""
            profile.alias_address = (
                f"{profile.alias_name}@{domain}"
                if profile.alias_name and domain
                else profile.alias_name or _("Alias domain not configured")
            )

    def _compute_metrics(self):
        Document = self.env["ai.processing.document"]
        Attempt = self.env["ai.processing.attempt"]
        for profile in self:
            domain = [("company_id", "=", profile.company_id.id)]
            profile.processed_count = Document.search_count(
                domain + [("state", "in", ("invoice", "other"))]
            )
            profile.pending_count = Document.search_count(
                domain + [("state", "in", ("pending", "reserved"))]
            )
            profile.failed_count = Attempt.search_count(
                domain + [("outcome", "=", "failure")]
            )
            profile.fallback_success_count = Attempt.search_count(
                domain + [("outcome", "=", "success"), ("role", "=", "fallback")]
            )

    def _compute_help(self):
        for profile in self:
            profile.guide_html = Markup(
                """
                <section>
                  <h2>Inicio rápido</h2>
                  <ol>
                    <li>Elija el protocolo que habla su servidor y revise la URL.</li>
                    <li>Use una variable de entorno para la clave o un servidor
                    propio sin clave cuando su política lo permita.</li>
                    <li>Pulse <strong>Probar conexión y leer modelos</strong>.</li>
                    <li>Abra <strong>Modelos</strong>, ejecute la sonda visual y
                    elija principal y respaldo.</li>
                    <li>Cree un buzón compartido, por ejemplo
                    <code>facturas@empresa.com</code>, y conéctelo a Odoo por
                    IMAP con el modelo <code>ai.processing.inbox</code> y los
                    adjuntos activados.</li>
                    <li>Configure remitentes, límites y consentimiento.</li>
                    <li>Guarde y envíe una factura de prueba conocida al buzón
                    o alias configurado.</li>
                  </ol>
                  <h2>Trabajo diario</h2>
                  <ol>
                    <li>Abra <strong>Bandeja de facturas</strong>.</li>
                    <li>Procese candidatos si el perfil está en modo manual.</li>
                    <li>Abra el borrador y compare el PDF con la pestaña
                    <strong>AI Processing</strong>.</li>
                    <li>Revise proveedor, NIF/VAT, referencia, fechas, conceptos,
                    moneda, impuestos, totales, destinatario y duplicados.</li>
                    <li>Pulse <strong>Aplicar al borrador</strong> solo si todo
                    coincide. Después complete la revisión contable habitual.</li>
                  </ol>
                  <p><strong>Importante:</strong> la IA nunca publica, paga, crea
                  proveedores ni decide cuentas o impuestos.</p>
                </section>
                """
            )
            profile.faq_html = Markup(
                """
                <section>
                  <h2>Preguntas frecuentes</h2>
                  <h3>¿Puedo usar mi propio servidor?</h3>
                  <p>Sí. Seleccione OpenAI-compatible u Ollama, indique la URL completa
                  y permita red privada sólo si controla ese servidor.</p>
                  <h3>¿Dónde pongo la clave?</h3>
                  <p>El campo de variable espera un nombre como
                  <code>OLLAMA_API_KEY</code>, no la clave. Configure el valor en
                  el entorno del servidor. Una clave pegada requiere
                  <code>AI_PROCESSING_MASTER_KEY</code>.</p>
                  <h3>¿Por qué no puedo elegir un modelo?</h3>
                  <p>Debe estar disponible y tener visión/documentos declarados,
                  verificados mediante sonda o aprobados por un administrador.</p>
                  <h3>¿Qué formatos se procesan?</h3>
                  <p>PDF, JPEG, PNG y WebP. GIF y otros formatos se conservan,
                  pero no se envían al modelo.</p>
                  <h3>¿Qué ocurre con GIF, firmas y logos?</h3>
                  <p>Se conservan con una explicación, pero no se envían al modelo.</p>
                  <h3>¿Qué ocurre con varios adjuntos?</h3>
                  <p>Cada archivo válido es un trabajo independiente. El fallo de
                  uno no cancela los demás.</p>
                  <h3>¿Qué cuenta de correo debo usar?</h3>
                  <p>Para recibir, use un buzón compartido y dedicado, como
                  <code>facturas@empresa.com</code>, conectado a Odoo por IMAP.
                  Para enviar sirve cualquier cuenta cuyo dominio esté permitido.
                  No se necesita SMTP saliente para procesar facturas.</p>
                  <h3>¿Cuándo se usa el respaldo?</h3>
                  <p>Ante fallos temporales o una salida estructurada inválida.
                  No oculta claves erróneas, falta de consentimiento o bloqueos
                  de seguridad.</p>
                  <h3>¿Por qué no aparece Aplicar al borrador?</h3>
                  <p>Compruebe que sigue en borrador, el adjunto no cambió, el
                  destinatario coincide, no hay duplicado y existe un proveedor
                  con NIF/VAT exacto.</p>
                  <h3>¿Se aplican impuestos automáticamente?</h3>
                  <p>No. Los tipos extraídos son evidencia para revisión contable.</p>
                  <h3>¿Dónde reviso los errores?</h3>
                  <p>Abra <strong>Documentos</strong> para el motivo y
                  <strong>Historial</strong> para el modelo, duración, rol y
                  categoría del intento.</p>
                </section>
                """
            )

    def _alias_get_creation_values(self):
        """Describe the inbox record created by the Odoo 19 mail gateway."""
        values = super()._alias_get_creation_values()
        values["alias_model_id"] = self.env["ir.model"]._get_id(
            "ai.processing.inbox"
        )
        values["alias_contact"] = "everyone"
        if self:
            self.ensure_one()
            values["alias_defaults"] = repr({"company_id": self.company_id.id})
        return values

    def runtime_settings(self, model):
        self.ensure_one()
        return ProviderSettings(
            protocol=self.protocol,
            base_url=self.base_url,
            model=model.identifier,
            api_key=self._runtime_api_key(),
            timeout=self.timeout_seconds,
            temperature=model.temperature,
            max_output_tokens=model.max_output_tokens,
            allow_private=self.allow_private_endpoint,
            structured_mode=self.structured_mode,
            pdf_engine=self.pdf_engine,
            pdf_detail=self.pdf_detail,
        )

    def action_test_and_read_models(self):
        self.ensure_one()
        placeholder = self.env["ai.processing.engine.model"].new(
            {
                "identifier": "catalog-check",
                "temperature": 0,
                "max_output_tokens": 4000,
            }
        )
        try:
            values = ProviderGateway().list_models(self.runtime_settings(placeholder))
        except (ProviderError, EndpointPolicyError, UserError) as error:
            message = str(error)[:500]
            self.write(
                {
                    "connection_state": "error",
                    "last_catalog_sync": fields.Datetime.now(),
                    "last_connection_message": message,
                }
            )
            return self._notification(
                _("Connection failed"), message, "danger", sticky=True
            )
        Model = self.env["ai.processing.engine.model"]
        existing = Model.search(
            [("profile_id", "=", self.id), ("protocol", "=", self.protocol)]
        )
        existing.write({"available": False})
        by_identifier = {record.identifier: record for record in existing}
        for item in values:
            model_values = {
                "remote_label": item["label"],
                "available": True,
                "context_length": item["context_length"],
                "modalities": item["modalities"],
            }
            if item["declared_document_capable"]:
                model_values["capability_state"] = "declared"
            record = by_identifier.get(item["identifier"])
            if record:
                record.write(model_values)
            else:
                model_values.update(
                    {
                        "profile_id": self.id,
                        "protocol": self.protocol,
                        "identifier": item["identifier"],
                    }
                )
                Model.create(model_values)
        if self.primary_model_id and not self.primary_model_id.available:
            self.primary_model_id = False
        if self.fallback_model_id and not self.fallback_model_id.available:
            self.fallback_model_id = False
        message = _(
            "%(total)s models read; %(capable)s currently approved for documents.",
            total=len(values),
            capable=len(
                self.model_ids.filtered(
                    lambda item: item.available and item.document_capable
                )
            ),
        )
        self.write(
            {
                "connection_state": "ok",
                "last_catalog_sync": fields.Datetime.now(),
                "last_connection_message": message,
            }
        )
        return self._notification(_("Catalog updated"), message, "success")

    def action_save_configuration(self):
        self.ensure_one()
        if self.alias_id:
            self.alias_id.sudo().write(self._alias_get_creation_values())
        return self._notification(
            _("Configuration saved"),
            _(
                "Changes are active. AI Processing never posts or pays invoices automatically."
            ),
            "success",
        )

    def action_open_models(self):
        self.ensure_one()
        action = self.env.ref("ai_processing.action_ai_processing_models").read()[0]
        action["domain"] = [("profile_id", "=", self.id)]
        action["context"] = {
            "default_profile_id": self.id,
            "default_protocol": self.protocol,
        }
        return action

    def action_open_inbox(self):
        self.ensure_one()
        action = self.env.ref("ai_processing.action_ai_processing_inbox").read()[0]
        action["domain"] = [("company_id", "=", self.company_id.id)]
        return action

    @api.model
    def action_open_company_profile(self):
        profile = self.search([("company_id", "=", self.env.company.id)], limit=1)
        if not profile:
            profile = self.create(
                {
                    "company_id": self.env.company.id,
                    "alias_name": f"ai-invoices-{self.env.company.id}",
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("AI Processing"),
            "res_model": self._name,
            "view_mode": "form",
            "res_id": profile.id,
            "target": "current",
        }

    @staticmethod
    def _notification(title, message, level, sticky=False):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": level,
                "sticky": sticky,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
