import base64
import io

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from PIL import Image

from ..core.contracts import normalize_result


def png_bytes(size=(600, 800)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, "PNG")
    return buffer.getvalue()


def extracted_payload(company):
    return normalize_result(
        {
            "kind": "supplier_invoice",
            "supplier": {
                "name": "Proveedor de prueba",
                "tax_id": "ESA12345678",
                "email": None,
                "iban": None,
            },
            "recipient_evidence": {
                "name": company.name,
                "tax_id": company.vat,
            },
            "reference": "AIP-TEST-001",
            "issued_on": "2026-07-29",
            "due_on": None,
            "currency_code": company.currency_id.name,
            "payment_reference": None,
            "expense_class": "insurance",
            "tax_hint": "domestic_deductible",
            "amounts": {"net": 100, "tax": 21, "gross": 121},
            "items": [
                {
                    "label": "Seguro RC profesional",
                    "quantity": 1,
                    "unit_price": 100,
                    "net_amount": 100,
                    "tax_percent": 21,
                    "discount_percent": None,
                }
            ],
            "confidence": 0.98,
            "alerts": [],
        },
        {
            "name": company.name,
            "tax_id": company.vat,
            "country_code": company.country_id.code,
            "currency_code": company.currency_id.name,
        },
    )


@tagged("post_install", "-at_install")
class TestAIProcessing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.vat = "ESB87654321"
        alias_values = cls.env[
            "ai.processing.profile"
        ]._alias_get_creation_values()
        if not alias_values.get("alias_model_id"):
            raise AssertionError(
                "The Odoo mail alias must target ai.processing.inbox."
            )
        cls.profile = cls.env["ai.processing.profile"].create(
            {
                "company_id": cls.company.id,
                "alias_name": f"aip-test-{cls.company.id}",
                "mode": "manual",
            }
        )
        if cls.profile.alias_model_id.model != "ai.processing.inbox":
            raise AssertionError("The created alias targets the wrong Odoo model.")
        cls.model = cls.env["ai.processing.engine.model"].create(
            {
                "profile_id": cls.profile.id,
                "protocol": "ollama",
                "identifier": "vision-test",
                "capability_state": "verified",
            }
        )
        cls.profile.write(
            {
                "primary_model_id": cls.model.id,
                "connection_state": "ok",
                "transfer_consent": True,
            }
        )

    def _attachment(self, raw=None, name="invoice.png"):
        raw = raw if raw is not None else png_bytes()
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "datas": base64.b64encode(raw),
                "mimetype": "image/png",
            }
        )

    def test_profile_is_unique_per_company(self):
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                self.env["ai.processing.profile"].create(
                    {
                        "company_id": self.company.id,
                        "alias_name": "duplicate-profile",
                    }
                )

    def test_sender_domain_normalization(self):
        self.profile.allowed_sender_domains = "Proveedor.ES, @xn--espaa-rta.es"
        self.assertEqual(
            self.profile.normalized_sender_domains(),
            ["proveedor.es", "xn--espaa-rta.es"],
        )
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                self.profile.allowed_sender_domains = "not-a-domain"

    def test_document_classification_and_duplicate(self):
        attachment = self._attachment()
        first = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=attachment,
        )
        self.assertEqual(first.state, "candidate")
        second_attachment = self._attachment()
        second = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=second_attachment,
        )
        self.assertEqual(second.state, "duplicate")
        self.assertEqual(second.duplicate_of_id, first)

    def test_small_image_and_gif_are_not_processed(self):
        small = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=self._attachment(png_bytes((100, 100)), "logo.png"),
        )
        self.assertEqual(small.state, "ignored")
        gif = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=self._attachment(b"GIF89a" + b"x" * 100, "signature.gif"),
        )
        self.assertEqual(gif.state, "ignored")
        self.assertEqual(gif.detected_mimetype, "image/gif")

    def test_staging_does_not_change_accounting_fields(self):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")],
            limit=1,
        )
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": journal.id,
                "move_type": "in_invoice",
            }
        )
        attachment = self._attachment(name="staging.png")
        attachment.write({"res_model": "account.move", "res_id": move.id})
        move._message_set_main_attachment_id(attachment, force=True, filter_xml=False)
        document = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=attachment,
            move=move,
        )
        result = extracted_payload(self.company)
        result["_runtime"] = {
            "protocol": "ollama",
            "model": self.model.identifier,
            "model_id": self.model.id,
            "role": "primary",
        }
        move._aip_stage_result(document, result)
        self.assertFalse(move.partner_id)
        self.assertFalse(move.invoice_line_ids)
        self.assertEqual(move.aip_state, "ready")

    def test_apply_requires_exact_supplier_and_keeps_draft(self):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")],
            limit=1,
        )
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": journal.id,
                "move_type": "in_invoice",
            }
        )
        attachment = self._attachment(name="apply.png")
        attachment.write({"res_model": "account.move", "res_id": move.id})
        move._message_set_main_attachment_id(attachment, force=True, filter_xml=False)
        document = self.env["ai.processing.document"].create_from_attachment(
            company=self.company,
            attachment=attachment,
            move=move,
        )
        result = extracted_payload(self.company)
        result["_runtime"] = {
            "protocol": "ollama",
            "model": self.model.identifier,
            "model_id": self.model.id,
            "role": "primary",
        }
        move._aip_stage_result(document, result)
        with self.assertRaises(UserError):
            move.action_aip_apply()
        supplier = self.env["res.partner"].create(
            {"name": "Proveedor de prueba", "vat": "ES A12345678"}
        )
        move.action_aip_apply()
        self.assertEqual(move.partner_id, supplier)
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.aip_state, "applied")
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertTrue(move.invoice_line_ids.aip_imported)
        self.assertFalse(move.invoice_line_ids.tax_ids)
