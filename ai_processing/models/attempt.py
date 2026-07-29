from odoo import fields, models


class AIProcessingAttempt(models.Model):
    _name = "ai.processing.attempt"
    _description = "AI Processing immutable attempt"
    _order = "started_at desc, id desc"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        required=True,
        ondelete="cascade",
        index=True,
    )
    document_id = fields.Many2one(
        "ai.processing.document",
        ondelete="set null",
        index=True,
        check_company=True,
    )
    move_id = fields.Many2one(
        "account.move",
        ondelete="set null",
        index=True,
        check_company=True,
    )
    model_id = fields.Many2one(
        "ai.processing.engine.model",
        ondelete="set null",
        index=True,
        check_company=True,
    )
    protocol = fields.Char(required=True, index=True)
    model_identifier = fields.Char(required=True, index=True)
    role = fields.Selection(
        [("primary", "Primary"), ("fallback", "Fallback")],
        required=True,
        index=True,
    )
    outcome = fields.Selection(
        [("success", "Success"), ("failure", "Failure")],
        required=True,
        index=True,
    )
    error_category = fields.Char(index=True)
    safe_error = fields.Char()
    started_at = fields.Datetime(required=True, index=True)
    finished_at = fields.Datetime(required=True)
    duration_ms = fields.Integer()
    document_checksum = fields.Char(index=True)
    contract_version = fields.Char(required=True)
    prompt_version = fields.Char(required=True)
