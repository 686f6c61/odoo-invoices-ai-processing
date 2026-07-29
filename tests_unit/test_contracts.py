import json
import unittest

from ai_processing.core.contracts import (
    ContractError,
    arithmetic_check,
    normalize_result,
    parse_result,
)


def valid_payload():
    return {
        "kind": "supplier_invoice",
        "supplier": {
            "name": "Proveedor Uno",
            "tax_id": "ESA12345678",
            "email": None,
            "iban": None,
        },
        "recipient_evidence": {"name": "00B", "tax_id": "ESB87654321"},
        "reference": "F-2026-001",
        "issued_on": "2026-07-29",
        "due_on": None,
        "currency_code": "eur",
        "payment_reference": None,
        "expense_class": "insurance",
        "tax_hint": "domestic_deductible",
        "amounts": {"net": 100.0, "tax": 21.0, "gross": 121.0},
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
        "confidence": 0.97,
        "alerts": [],
    }


class ContractTests(unittest.TestCase):
    def test_valid_payload(self):
        result = parse_result(json.dumps(valid_payload()))
        self.assertEqual(result["expense_class"], "insurance")

    def test_exact_markdown_fence_is_tolerated(self):
        result = parse_result(f"```json\n{json.dumps(valid_payload())}\n```")
        self.assertEqual(result["reference"], "F-2026-001")

    def test_commentary_outside_fence_is_rejected(self):
        with self.assertRaises(ContractError):
            parse_result(f"Result:\n```json\n{json.dumps(valid_payload())}\n```")

    def test_unknown_property_is_rejected(self):
        payload = valid_payload()
        payload["instructions"] = "post it"
        with self.assertRaises(ContractError):
            parse_result(json.dumps(payload))

    def test_non_finite_number_is_rejected(self):
        payload = valid_payload()
        payload["confidence"] = float("nan")
        with self.assertRaises(ContractError):
            parse_result(json.dumps(payload))

    def test_normalization_preserves_company_authority(self):
        result = normalize_result(
            valid_payload(),
            {
                "name": "Mi Empresa",
                "tax_id": "ESB87654321",
                "country_code": "ES",
                "currency_code": "EUR",
            },
        )
        self.assertEqual(result["_company"]["name"], "Mi Empresa")
        self.assertTrue(result["_local_checks"]["recipient_matches"])
        self.assertTrue(result["_local_checks"]["arithmetic_ok"])
        self.assertEqual(result["currency_code"], "EUR")

    def test_mismatched_recipient_is_blocking_evidence(self):
        payload = valid_payload()
        payload["recipient_evidence"]["tax_id"] = "ESX00000000"
        result = normalize_result(
            payload,
            {
                "name": "Mi Empresa",
                "tax_id": "ESB87654321",
                "country_code": "ES",
                "currency_code": "EUR",
            },
        )
        self.assertFalse(result["_local_checks"]["recipient_matches"])
        self.assertTrue(any("differs" in item for item in result["alerts"]))

    def test_arithmetic_failure(self):
        payload = valid_payload()
        payload["amounts"]["gross"] = 999
        self.assertFalse(arithmetic_check(payload))


if __name__ == "__main__":
    unittest.main()
