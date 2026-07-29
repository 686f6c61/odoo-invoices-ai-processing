import hashlib
import logging
import time
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from ..core import ContractError, ProviderError, ProviderGateway, parse_result
from ..core.contracts import normalize_result
from ..core.document_io import inspect_document, render_pdf
from ..core.prompts import PROMPT_VERSION, build_prompts

_logger = logging.getLogger(__name__)
CONTRACT_VERSION = "2026-07-29.1"


class AIProcessingDocument(models.Model):
    _name = "ai.processing.document"
    _description = "AI Processing document work item"
    _order = "received_at desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, readonly=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        ondelete="cascade",
        index=True,
    )
    inbox_id = fields.Many2one(
        "ai.processing.inbox",
        readonly=True,
        ondelete="set null",
        index=True,
        check_company=True,
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        required=True,
        readonly=True,
        ondelete="restrict",
        index=True,
    )
    move_id = fields.Many2one(
        "account.move",
        readonly=True,
        copy=False,
        ondelete="set null",
        index=True,
        check_company=True,
    )
    received_at = fields.Datetime(
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        index=True,
    )
    declared_mimetype = fields.Char(readonly=True)
    detected_mimetype = fields.Char(readonly=True, index=True)
    checksum = fields.Char(required=True, readonly=True, index=True)
    byte_size = fields.Integer(readonly=True)
    image_width = fields.Integer(readonly=True)
    image_height = fields.Integer(readonly=True)
    page_count = fields.Integer(readonly=True)
    state = fields.Selection(
        [
            ("candidate", "Candidate"),
            ("pending", "Pending"),
            ("reserved", "Processing"),
            ("invoice", "Invoice detected"),
            ("other", "Not an invoice"),
            ("ignored", "Ignored"),
            ("duplicate", "Duplicate"),
            ("failed", "Failed"),
        ],
        default="candidate",
        required=True,
        readonly=True,
        index=True,
    )
    decision_reason = fields.Char(readonly=True)
    result_payload = fields.Json(readonly=True, copy=False)
    safe_error = fields.Text(readonly=True, copy=False)
    attempt_count = fields.Integer(readonly=True, copy=False)
    reserved_at = fields.Datetime(readonly=True, copy=False, index=True)
    completed_at = fields.Datetime(readonly=True, copy=False)
    duplicate_of_id = fields.Many2one(
        "ai.processing.document",
        readonly=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )
    attempt_ids = fields.One2many(
        "ai.processing.attempt",
        "document_id",
        readonly=True,
    )

    @api.model
    def create_from_attachment(self, *, company, attachment, inbox=None, move=None):
        raw = attachment.raw or b""
        profile = self.env["ai.processing.profile"].search(
            [("company_id", "=", company.id)],
            limit=1,
        )
        max_mb = profile.max_document_mb if profile else 12
        max_pages = profile.max_pdf_pages if profile else 20
        info = inspect_document(
            raw,
            max_bytes=max_mb * 1024 * 1024,
            max_pdf_pages=max_pages,
        )
        values = {
            "name": (attachment.name or _("Attachment without name"))[:500],
            "company_id": company.id,
            "inbox_id": inbox.id if inbox else False,
            "move_id": move.id if move else False,
            "attachment_id": attachment.id,
            "declared_mimetype": (attachment.mimetype or "")[:255],
            "detected_mimetype": info.mimetype,
            "checksum": hashlib.sha256(raw).hexdigest(),
            "byte_size": len(raw),
            "image_width": info.width,
            "image_height": info.height,
            "page_count": info.page_count,
            "state": "candidate" if info.eligible else "ignored",
            "decision_reason": info.reason[:500],
        }
        document = self.create(values)
        if document.state == "candidate":
            duplicate = document._find_duplicate()
            if duplicate:
                document.write(
                    {
                        "state": "duplicate",
                        "duplicate_of_id": duplicate.id,
                        "decision_reason": _(
                            "The same file already exists in this company."
                        ),
                    }
                )
            elif profile and profile.mode == "automatic" and profile.setup_ready:
                document.write(
                    {
                        "state": "pending",
                        "decision_reason": _("Waiting for AI Processing."),
                    }
                )
        return document

    def _find_duplicate(self):
        self.ensure_one()
        return self.search(
            [
                ("id", "!=", self.id),
                ("company_id", "=", self.company_id.id),
                ("checksum", "=", self.checksum),
                ("state", "!=", "failed"),
            ],
            order="id",
            limit=1,
        )

    def action_queue(self):
        self._check_accounting_access()
        for document in self:
            if document.state not in {"candidate", "failed", "other"}:
                continue
            profile = document._profile()
            if profile.mode == "off":
                raise UserError(_("AI Processing is disabled for this company."))
            if not profile.setup_ready:
                raise UserError(
                    _("Complete service, model and consent configuration first.")
                )
            document.write(
                {
                    "state": "pending",
                    "decision_reason": _("Waiting for AI Processing."),
                    "safe_error": False,
                    "completed_at": False,
                }
            )
        return True

    def action_ignore(self):
        self._check_accounting_access()
        self.filtered(
            lambda item: item.state not in {"invoice", "duplicate", "reserved"}
        ).write(
            {
                "state": "ignored",
                "decision_reason": _("Ignored manually."),
                "safe_error": False,
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_open_move(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("This document has no accounting draft."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def cron_process_pending(self, limit=20):
        stale_before = fields.Datetime.now() - timedelta(minutes=20)
        self.search(
            [("state", "=", "reserved"), ("reserved_at", "<", stale_before)],
            limit=100,
        ).write(
            {
                "state": "pending",
                "decision_reason": _("Interrupted work returned to the queue."),
            }
        )
        self.env.cr.execute(
            """
            SELECT id
              FROM ai_processing_document
             WHERE state = 'pending'
             ORDER BY id
             FOR UPDATE SKIP LOCKED
             LIMIT %s
            """,
            [max(1, min(int(limit or 20), 100))],
        )
        candidates = self.browse([row[0] for row in self.env.cr.fetchall()])
        allowed = self._apply_email_rate_limit(candidates)
        for document in allowed:
            try:
                with self.env.cr.savepoint():
                    document._process_reserved()
            except Exception as error:
                _logger.exception(
                    "Unhandled AI Processing failure for document %s", document.id
                )
                document.write(
                    {
                        "state": "failed",
                        "decision_reason": _("Processing failed."),
                        "safe_error": self._safe_message(error),
                        "completed_at": fields.Datetime.now(),
                    }
                )
                if document.move_id and document.move_id.state == "draft":
                    document.move_id.write(
                        {
                            "aip_state": "failed",
                            "aip_message": self._safe_message(error),
                            "aip_last_analysis_at": fields.Datetime.now(),
                        }
                    )
        return True

    def _apply_email_rate_limit(self, candidates):
        allowed = self.browse()
        seen = {}
        for document in candidates:
            profile = document._profile()
            key = document.inbox_id.id if document.inbox_id else f"direct-{document.id}"
            company_seen = seen.setdefault(document.company_id.id, [])
            if key not in company_seen:
                if len(company_seen) >= profile.emails_per_minute:
                    continue
                company_seen.append(key)
            allowed |= document
        return allowed

    def _process_reserved(self):
        self.ensure_one()
        if self.state != "pending":
            return False
        profile = self._profile()
        if not profile.setup_ready or profile.mode == "off":
            raise UserError(_("AI Processing configuration is no longer ready."))
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            [f"aip:{self.company_id.id}:{self.checksum}"],
        )
        duplicate = self._find_duplicate()
        if duplicate and duplicate.id < self.id:
            self.write(
                {
                    "state": "duplicate",
                    "duplicate_of_id": duplicate.id,
                    "decision_reason": _("The same file was processed earlier."),
                    "completed_at": fields.Datetime.now(),
                }
            )
            return False
        self.write(
            {
                "state": "reserved",
                "reserved_at": fields.Datetime.now(),
                "attempt_count": self.attempt_count + 1,
                "safe_error": False,
            }
        )
        if self.move_id and self.move_id.state == "draft":
            self.move_id.write(
                {
                    "aip_state": "analyzing",
                    "aip_message": _("Analyzing the current attachment."),
                    "aip_last_analysis_at": fields.Datetime.now(),
                }
            )
        payload = self._analyze(profile)
        if payload["kind"] not in {"supplier_invoice", "supplier_credit"}:
            self.write(
                {
                    "state": "other",
                    "decision_reason": _(
                        "The document was not confirmed as a supplier invoice."
                    ),
                    "result_payload": payload,
                    "completed_at": fields.Datetime.now(),
                }
            )
            return True
        move = self.move_id or self._create_draft(payload)
        move._aip_stage_result(self, payload)
        self.write(
            {
                "state": "invoice",
                "move_id": move.id,
                "decision_reason": _(
                    "Invoice detected; draft ready for accounting review."
                ),
                "result_payload": payload,
                "completed_at": fields.Datetime.now(),
            }
        )
        return True

    def _analyze(self, profile):
        raw = self.attachment_id.raw or b""
        rendered = None
        if self.detected_mimetype == "application/pdf" and profile.protocol in {
            "ollama",
            "openai_compatible",
        }:
            rendered = render_pdf(raw, max_pages=profile.max_visual_pages)
        company = {
            "name": self.company_id.name,
            "tax_id": self.company_id.vat,
            "country_code": self.company_id.country_id.code,
            "currency_code": self.company_id.currency_id.name,
        }
        system_prompt, user_prompt = build_prompts(company, profile.company_guidance)
        chain = [
            ("primary", profile.primary_model_id),
            ("fallback", profile.fallback_model_id),
        ]
        errors = []
        for role, model in chain:
            if not model:
                continue
            started_at = fields.Datetime.now()
            started_clock = time.monotonic()
            try:
                text = ProviderGateway().analyze(
                    profile.runtime_settings(model),
                    filename=self.name,
                    mimetype=self.detected_mimetype,
                    raw=raw,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    rendered_pages=rendered,
                )
                payload = normalize_result(parse_result(text), company)
            except ContractError as error:
                self._record_attempt(
                    profile,
                    model,
                    role,
                    "failure",
                    "contract",
                    error,
                    started_at,
                    started_clock,
                )
                errors.append(str(error))
                continue
            except ProviderError as error:
                self._record_attempt(
                    profile,
                    model,
                    role,
                    "failure",
                    error.category,
                    error,
                    started_at,
                    started_clock,
                )
                errors.append(str(error))
                if not error.retryable and error.category != "request":
                    break
                continue
            self._record_attempt(
                profile,
                model,
                role,
                "success",
                False,
                False,
                started_at,
                started_clock,
            )
            payload["_runtime"] = {
                "protocol": profile.protocol,
                "model": model.identifier,
                "model_id": model.id,
                "role": role,
            }
            return payload
        raise UserError(
            _(
                "No configured model produced a valid result. %s",
                errors[-1] if errors else "",
            )
        )

    def _record_attempt(
        self,
        profile,
        model,
        role,
        outcome,
        category,
        error,
        started_at,
        started_clock,
    ):
        self.env["ai.processing.attempt"].sudo().create(
            {
                "company_id": self.company_id.id,
                "document_id": self.id,
                "move_id": self.move_id.id if self.move_id else False,
                "model_id": model.id,
                "protocol": profile.protocol,
                "model_identifier": model.identifier,
                "role": role,
                "outcome": outcome,
                "error_category": category or False,
                "safe_error": self._safe_message(error) if error else False,
                "started_at": started_at,
                "finished_at": fields.Datetime.now(),
                "duration_ms": max(0, int((time.monotonic() - started_clock) * 1000)),
                "document_checksum": self.checksum,
                "contract_version": CONTRACT_VERSION,
                "prompt_version": PROMPT_VERSION,
            }
        )

    def _create_draft(self, payload):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company_id.id), ("type", "=", "purchase")],
            order="sequence, id",
            limit=1,
        )
        if not journal:
            raise UserError(_("No purchase journal is configured for this company."))
        move = (
            self.env["account.move"]
            .with_company(self.company_id)
            .create(
                {
                    "company_id": self.company_id.id,
                    "journal_id": journal.id,
                    "move_type": "in_refund"
                    if payload["kind"] == "supplier_credit"
                    else "in_invoice",
                    "aip_state": "analyzing",
                    "aip_document_id": self.id,
                }
            )
        )
        copied = self.attachment_id.with_context(aip_skip_intake=True).copy(
            {"res_model": "account.move", "res_id": move.id}
        )
        move.with_context(aip_skip_intake=True)._message_set_main_attachment_id(
            copied,
            force=True,
            filter_xml=False,
        )
        return move

    def _profile(self):
        self.ensure_one()
        profile = self.env["ai.processing.profile"].search(
            [("company_id", "=", self.company_id.id)],
            limit=1,
        )
        if not profile:
            raise UserError(_("No AI Processing profile exists for this company."))
        return profile

    def _check_accounting_access(self):
        if not self.env.user.has_group("account.group_account_invoice"):
            raise AccessError(
                _("Only accounting users can manage AI Processing documents.")
            )

    @staticmethod
    def _safe_message(error):
        if not error:
            return ""
        value = (
            error.args[0]
            if error.args and isinstance(error.args[0], str)
            else str(error)
        )
        return value[:500]
