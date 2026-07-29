import hashlib
import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

IDENTIFIER_PATTERN = re.compile(r"[^A-Z0-9]")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    aip_imported = fields.Boolean(
        string="Imported by AI Processing",
        readonly=True,
        copy=False,
        index=True,
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    aip_state = fields.Selection(
        [
            ("not_analyzed", "Not analyzed"),
            ("pending", "Pending"),
            ("analyzing", "Analyzing"),
            ("ready", "Ready for review"),
            ("warning", "Review required"),
            ("failed", "Failed"),
            ("applied", "Applied to draft"),
        ],
        default="not_analyzed",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    aip_message = fields.Text(readonly=True, copy=False)
    aip_result = fields.Json(readonly=True, copy=False)
    aip_protocol = fields.Char(readonly=True, copy=False)
    aip_model_identifier = fields.Char(readonly=True, copy=False)
    aip_model_role = fields.Selection(
        [("primary", "Primary"), ("fallback", "Fallback")],
        readonly=True,
        copy=False,
    )
    aip_model_id = fields.Many2one(
        "ai.processing.engine.model",
        readonly=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )
    aip_document_id = fields.Many2one(
        "ai.processing.document",
        readonly=True,
        copy=False,
        ondelete="set null",
        check_company=True,
        index=True,
    )
    aip_last_analysis_at = fields.Datetime(readonly=True, copy=False)
    aip_attachment_checksum = fields.Char(readonly=True, copy=False, index=True)
    aip_duplicate_move_id = fields.Many2one(
        "account.move",
        readonly=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )
    aip_can_analyze = fields.Boolean(compute="_compute_aip_actions")
    aip_can_apply = fields.Boolean(compute="_compute_aip_actions")
    aip_attempt_ids = fields.One2many(
        "ai.processing.attempt",
        "move_id",
        readonly=True,
    )

    @api.depends(
        "move_type",
        "state",
        "message_main_attachment_id",
        "aip_state",
        "aip_result",
        "aip_duplicate_move_id",
        "aip_attachment_checksum",
    )
    def _compute_aip_actions(self):
        for move in self:
            supported = move.move_type in {"in_invoice", "in_refund", "in_receipt"}
            has_attachment = bool(move.message_main_attachment_id)
            move.aip_can_analyze = bool(
                supported
                and move.state == "draft"
                and has_attachment
                and move.aip_state not in {"pending", "analyzing"}
            )
            checks = (move.aip_result or {}).get("_local_checks") or {}
            current_checksum = move._aip_current_checksum()
            move.aip_can_apply = bool(
                supported
                and move.state == "draft"
                and move.aip_state in {"ready", "warning"}
                and move.aip_result
                and not move.aip_duplicate_move_id
                and checks.get("recipient_matches") is not False
                and current_checksum
                and current_checksum == move.aip_attachment_checksum
            )

    def action_aip_queue(self):
        self._aip_check_accounting_access()
        for move in self:
            if not move.aip_can_analyze:
                continue
            attachment = move.message_main_attachment_id
            document = self.env["ai.processing.document"].search(
                [
                    ("move_id", "=", move.id),
                    ("attachment_id", "=", attachment.id),
                ],
                limit=1,
            )
            if not document:
                document = self.env["ai.processing.document"].create_from_attachment(
                    company=move.company_id,
                    attachment=attachment,
                    move=move,
                )
            if document.state == "duplicate":
                raise UserError(_("This file is already present in the company."))
            if document.state == "ignored":
                raise UserError(document.decision_reason)
            document.action_queue()
            move.write(
                {
                    "aip_state": "pending",
                    "aip_message": _("Waiting for AI Processing."),
                    "aip_document_id": document.id,
                    "aip_result": False,
                    "aip_duplicate_move_id": False,
                }
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("AI Processing"),
                "message": _(
                    "Selected supplier drafts were added to the processing queue."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def _aip_stage_result(self, document, result):
        self.ensure_one()
        runtime = result.get("_runtime") or {}
        duplicate = self._aip_find_duplicate(document, result)
        alerts = list(result.get("alerts") or [])
        profile = self.env["ai.processing.profile"].search(
            [("company_id", "=", self.company_id.id)],
            limit=1,
        )
        threshold = profile.confidence_threshold if profile else 0.75
        if result.get("confidence", 0) < threshold:
            alerts.append(_("Model confidence is below %.2f.", threshold))
        if duplicate:
            alerts.append(_("Possible duplicate of %s.", duplicate.display_name))
        state = "warning" if alerts else "ready"
        self.write(
            {
                "aip_state": state,
                "aip_message": "\n".join(dict.fromkeys(alerts)) or False,
                "aip_result": result,
                "aip_protocol": runtime.get("protocol"),
                "aip_model_identifier": runtime.get("model"),
                "aip_model_id": runtime.get("model_id") or False,
                "aip_model_role": runtime.get("role"),
                "aip_document_id": document.id,
                "aip_last_analysis_at": fields.Datetime.now(),
                "aip_attachment_checksum": document.checksum,
                "aip_duplicate_move_id": duplicate.id if duplicate else False,
            }
        )
        if document.move_id != self:
            document.move_id = self
        return True

    def _aip_find_duplicate(self, document, result):
        self.ensure_one()
        base = [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
            ("move_type", "in", ("in_invoice", "in_refund", "in_receipt")),
            ("state", "!=", "cancel"),
        ]
        duplicate = self.search(
            base + [("aip_attachment_checksum", "=", document.checksum)],
            limit=1,
        )
        if duplicate:
            return duplicate
        supplier = result.get("supplier") or {}
        tax_id = self._aip_normalize_identifier(supplier.get("tax_id"))
        reference = result.get("reference")
        if not tax_id or not reference:
            return self.browse()
        partner = (
            self.env["res.partner"]
            .search(
                [
                    ("company_id", "in", (False, self.company_id.id)),
                    ("vat", "!=", False),
                ]
            )
            .filtered(lambda item: self._aip_normalize_identifier(item.vat) == tax_id)[
                :1
            ]
        )
        if not partner:
            return self.browse()
        return self.search(
            base + [("partner_id", "=", partner.id), ("ref", "=ilike", reference)],
            limit=1,
        )

    def action_aip_apply(self):
        self.ensure_one()
        self._aip_check_accounting_access()
        if not self.aip_can_apply:
            raise UserError(
                _(
                    "The result cannot be applied. Resolve attachment, recipient or duplicate warnings first."
                )
            )
        result = self.aip_result or {}
        supplier = result.get("supplier") or {}
        partner = self._aip_exact_partner(supplier.get("tax_id"))
        if not partner:
            raise UserError(
                _(
                    "No supplier with the exact extracted VAT/NIF exists. Create or select it manually first."
                )
            )
        existing = self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        if existing:
            raise UserError(
                _(
                    "Existing invoice lines were preserved. Remove them manually before applying the result."
                )
            )
        values = {"partner_id": partner.id}
        if result.get("kind") == "supplier_credit":
            values["move_type"] = "in_refund"
        if result.get("reference"):
            values["ref"] = result["reference"]
        if result.get("issued_on"):
            values["invoice_date"] = result["issued_on"]
        if result.get("due_on"):
            values["invoice_date_due"] = result["due_on"]
        if result.get("payment_reference"):
            values["payment_reference"] = result["payment_reference"]
        currency = self.env["res.currency"].search(
            [
                ("name", "=", (result.get("currency_code") or "").upper()),
                ("active", "=", True),
            ],
            limit=1,
        )
        if currency:
            values["currency_id"] = currency.id
        commands = []
        for item in result.get("items") or []:
            commands.append(
                (
                    0,
                    0,
                    {
                        "display_type": "product",
                        "name": item["label"],
                        "quantity": item["quantity"],
                        "price_unit": item["unit_price"],
                        "discount": item.get("discount_percent") or 0,
                        "tax_ids": [(5, 0, 0)],
                        "aip_imported": True,
                    },
                )
            )
        values["invoice_line_ids"] = commands
        self.write(values)
        self.write(
            {
                "aip_state": "applied",
                "aip_message": _(
                    "Extracted header and commercial lines were applied. Review accounts and taxes before posting."
                ),
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}

    def _aip_exact_partner(self, tax_id):
        normalized = self._aip_normalize_identifier(tax_id)
        if not normalized:
            return self.env["res.partner"]
        return (
            self.env["res.partner"]
            .search(
                [
                    ("company_id", "in", (False, self.company_id.id)),
                    ("vat", "!=", False),
                ]
            )
            .filtered(
                lambda item: self._aip_normalize_identifier(item.vat) == normalized
            )[:1]
        )

    def _aip_current_checksum(self):
        self.ensure_one()
        raw = (
            self.message_main_attachment_id.raw
            if self.message_main_attachment_id
            else b""
        )
        return hashlib.sha256(raw).hexdigest() if raw else ""

    def _aip_check_accounting_access(self):
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(
                _("Only accounting users can use AI Processing on supplier drafts.")
            )

    @staticmethod
    def _aip_normalize_identifier(value):
        return IDENTIFIER_PATTERN.sub("", str(value or "").upper())
