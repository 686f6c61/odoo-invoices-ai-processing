from email.utils import parseaddr

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AIProcessingInbox(models.Model):
    _name = "ai.processing.inbox"
    _description = "AI Processing incoming email"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "received_at desc, id desc"
    _check_company_auto = True
    _primary_email = "sender"

    subject = fields.Char(
        required=True, default=lambda self: _("Email without subject"), tracking=True
    )
    sender = fields.Char(readonly=True, tracking=True)
    recipients = fields.Char(readonly=True)
    message_identifier = fields.Char(readonly=True, copy=False, index=True)
    received_at = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
    document_ids = fields.One2many(
        "ai.processing.document",
        "inbox_id",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("received", "Received"),
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("review", "Accounting review"),
            ("complete", "Complete"),
            ("partial", "Partially complete"),
            ("failed", "Failed"),
        ],
        compute="_compute_summary",
        store=True,
        index=True,
    )
    document_count = fields.Integer(
        string="Preserved documents", compute="_compute_summary", store=True
    )
    eligible_count = fields.Integer(compute="_compute_summary", store=True)
    invoice_count = fields.Integer(compute="_compute_summary", store=True)
    ignored_count = fields.Integer(compute="_compute_summary", store=True)
    failure_count = fields.Integer(compute="_compute_summary", store=True)

    @api.depends("document_ids.state", "document_ids.move_id.aip_state")
    def _compute_summary(self):
        for inbox in self:
            documents = inbox.document_ids
            states = set(documents.mapped("state"))
            inbox.document_count = len(documents)
            inbox.eligible_count = len(
                documents.filtered(
                    lambda item: item.state in {"candidate", "pending", "reserved"}
                )
            )
            inbox.invoice_count = len(
                documents.filtered(lambda item: item.state == "invoice")
            )
            inbox.ignored_count = len(
                documents.filtered(lambda item: item.state in {"ignored", "duplicate"})
            )
            inbox.failure_count = len(
                documents.filtered(lambda item: item.state == "failed")
            )
            if not documents or states <= {"candidate"}:
                inbox.state = "received"
            elif "reserved" in states:
                inbox.state = "processing"
            elif states & {"pending", "candidate"}:
                inbox.state = "pending"
            elif "failed" in states:
                inbox.state = (
                    "partial"
                    if states - {"failed", "ignored", "duplicate"}
                    else "failed"
                )
            elif "invoice" in states:
                needs_review = documents.filtered(
                    lambda item: (
                        item.state == "invoice" and item.move_id.aip_state != "applied"
                    )
                )
                inbox.state = "review" if needs_review else "complete"
            else:
                inbox.state = "complete"

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        values = dict(custom_values or {})
        company = (
            self.env["res.company"]
            .browse(values.get("company_id") or self.env.company.id)
            .exists()
        )
        sender = (msg_dict.get("email_from") or "").strip()
        if company and not self._sender_allowed(company, sender):
            raise AccessError(
                _("The sender domain is not allowed for this invoice inbox.")
            )
        values.update(
            {
                "subject": (msg_dict.get("subject") or _("Email without subject"))[
                    :500
                ],
                "sender": sender[:500],
                "recipients": (msg_dict.get("to") or "")[:500],
                "message_identifier": (msg_dict.get("message_id") or "")[:500],
                "received_at": fields.Datetime.now(),
            }
        )
        return super().message_new(msg_dict, custom_values=values)

    @api.model
    def _sender_allowed(self, company, sender):
        profile = self.env["ai.processing.profile"].search(
            [("company_id", "=", company.id)],
            limit=1,
        )
        domains = profile.normalized_sender_domains() if profile else []
        if not domains:
            return True
        address = parseaddr(sender or "")[1].strip().lower()
        if "@" not in address:
            return False
        domain = address.rsplit("@", 1)[1].rstrip(".")
        try:
            domain = domain.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        return any(
            domain == allowed or domain.endswith(f".{allowed}") for allowed in domains
        )

    def _message_post_after_hook(self, message, msg_values):
        result = super()._message_post_after_hook(message, msg_values)
        if (
            message.message_type == "email"
            and message.attachment_ids
            and not self.env.context.get("aip_skip_intake")
        ):
            self._ingest_attachments(message.attachment_ids)
        return result

    def _ingest_attachments(self, attachments):
        Document = self.env["ai.processing.document"]
        for inbox in self:
            profile = self.env["ai.processing.profile"].search(
                [("company_id", "=", inbox.company_id.id)],
                limit=1,
            )
            maximum = profile.attachments_per_email if profile else 20
            known = set(inbox.document_ids.attachment_id.ids)
            eligible_seen = len(
                inbox.document_ids.filtered(
                    lambda item: (
                        item.state in {"candidate", "pending", "reserved", "invoice"}
                    )
                )
            )
            for attachment in attachments:
                if attachment.id in known:
                    continue
                document = Document.create_from_attachment(
                    company=inbox.company_id,
                    attachment=attachment,
                    inbox=inbox,
                )
                known.add(attachment.id)
                if document.state in {"candidate", "pending"}:
                    eligible_seen += 1
                    if eligible_seen > maximum:
                        document.write(
                            {
                                "state": "ignored",
                                "decision_reason": _(
                                    "Preserved without processing because this email exceeds the limit of %s eligible attachments.",
                                    maximum,
                                ),
                            }
                        )
        return True

    def action_queue_candidates(self):
        self._check_accounting_access()
        self.document_ids.filtered(
            lambda item: item.state in {"candidate", "failed", "other"}
        ).action_queue()
        return {"type": "ir.actions.client", "tag": "reload"}

    def _check_accounting_access(self):
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(
                _("Only accounting users can manage the AI Processing inbox.")
            )
