from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..core import ProviderError, ProviderGateway


class AIProcessingEngineModel(models.Model):
    _name = "ai.processing.engine.model"
    _description = "AI Processing model catalog entry"
    _order = "available desc, document_capable desc, identifier"
    _rec_name = "identifier"
    _check_company_auto = True

    profile_id = fields.Many2one(
        "ai.processing.profile",
        required=True,
        ondelete="cascade",
        index=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        related="profile_id.company_id", store=True, index=True
    )
    protocol = fields.Selection(
        [
            ("ollama", "Ollama local or Cloud"),
            ("openai", "OpenAI"),
            ("openrouter", "OpenRouter"),
            ("openai_compatible", "OpenAI-compatible server"),
        ],
        required=True,
        index=True,
    )
    identifier = fields.Char(required=True, index=True)
    remote_label = fields.Char()
    available = fields.Boolean(default=True, index=True)
    context_length = fields.Integer()
    modalities = fields.Char()
    capability_state = fields.Selection(
        [
            ("unknown", "Not verified"),
            ("declared", "Declared by service"),
            ("verified", "Passed visual probe"),
            ("approved", "Approved by administrator"),
            ("failed", "Probe failed"),
        ],
        default="unknown",
        required=True,
        index=True,
    )
    document_capable = fields.Boolean(
        compute="_compute_document_capable",
        store=True,
        index=True,
    )
    capability_checked_at = fields.Datetime(readonly=True)
    capability_message = fields.Char(readonly=True)
    temperature = fields.Float(default=0, digits=(3, 2))
    max_output_tokens = fields.Integer(default=4000)
    attempt_ids = fields.One2many("ai.processing.attempt", "model_id")
    attempt_count = fields.Integer(compute="_compute_metrics")
    success_count = fields.Integer(compute="_compute_metrics")
    failure_count = fields.Integer(compute="_compute_metrics")
    last_used_at = fields.Datetime(compute="_compute_metrics")

    _identifier_unique = models.Constraint(
        "unique(profile_id, protocol, identifier)",
        "This model already exists in the profile catalog.",
    )

    @api.depends("capability_state")
    def _compute_document_capable(self):
        for record in self:
            record.document_capable = record.capability_state in {
                "declared",
                "verified",
                "approved",
            }

    @api.depends("attempt_ids.outcome", "attempt_ids.finished_at")
    def _compute_metrics(self):
        for record in self:
            attempts = record.attempt_ids
            record.attempt_count = len(attempts)
            record.success_count = len(
                attempts.filtered(lambda item: item.outcome == "success")
            )
            record.failure_count = len(
                attempts.filtered(lambda item: item.outcome == "failure")
            )
            latest = attempts.sorted(
                key=lambda item: item.finished_at or item.create_date,
                reverse=True,
            )[:1]
            record.last_used_at = latest.finished_at if latest else False

    @api.constrains("temperature", "max_output_tokens")
    def _check_generation_settings(self):
        for record in self:
            if not 0 <= record.temperature <= 2:
                raise ValidationError(_("Temperature must be between 0 and 2."))
            if not 256 <= record.max_output_tokens <= 32768:
                raise ValidationError(_("Output tokens must be between 256 and 32768."))

    def action_probe_capability(self):
        self.ensure_one()
        try:
            passed = ProviderGateway().probe_document_capability(
                self.profile_id.runtime_settings(self)
            )
        except (ProviderError, UserError) as error:
            self.write(
                {
                    "capability_state": "failed",
                    "capability_checked_at": fields.Datetime.now(),
                    "capability_message": str(error)[:500],
                }
            )
            return self.profile_id._notification(
                _("Capability probe failed"),
                str(error)[:500],
                "danger",
                sticky=True,
            )
        values = {
            "capability_checked_at": fields.Datetime.now(),
            "capability_state": "verified" if passed else "failed",
            "capability_message": (
                _("The model read the visual verification code.")
                if passed
                else _(
                    "The model did not return the expected visual verification code."
                )
            ),
        }
        self.write(values)
        return self.profile_id._notification(
            _("Capability verified" if passed else "Capability not verified"),
            values["capability_message"],
            "success" if passed else "warning",
        )

    def action_admin_approve(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_("Only an administrator can approve a model manually."))
        self.write(
            {
                "capability_state": "approved",
                "capability_checked_at": fields.Datetime.now(),
                "capability_message": _(
                    "Approved manually by %s.", self.env.user.display_name
                ),
            }
        )
        return True

    def action_revoke_capability(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_("Only an administrator can revoke model approval."))
        for record in self:
            record.capability_state = "declared" if record.modalities else "unknown"
            record.capability_message = _("Manual approval revoked.")
        return True

    def action_back_to_profile(self):
        profile = self[:1].profile_id
        if not profile:
            return self.env["ai.processing.profile"].action_open_company_profile()
        return {
            "type": "ir.actions.act_window",
            "name": _("AI Processing configuration"),
            "res_model": "ai.processing.profile",
            "view_mode": "form",
            "res_id": profile.id,
            "target": "current",
        }
