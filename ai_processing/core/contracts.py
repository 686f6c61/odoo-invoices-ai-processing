import json
import math
import re
from datetime import date
from decimal import Decimal, InvalidOperation

EXPENSE_CLASSES = [
    "software_cloud_ai",
    "telecommunications",
    "subscriptions",
    "social_security",
    "professional_services",
    "travel_transport",
    "office_supplies",
    "insurance",
    "bank_charges",
    "other_services",
    "unknown",
]

TAX_HINTS = [
    "domestic_deductible",
    "domestic_non_deductible",
    "eu_reverse_charge",
    "non_eu_reverse_charge",
    "exempt",
    "outside_scope",
    "unknown",
]


def nullable(kind):
    return {"type": [kind, "null"]}


DOCUMENT_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "kind",
        "supplier",
        "recipient_evidence",
        "reference",
        "issued_on",
        "due_on",
        "currency_code",
        "payment_reference",
        "expense_class",
        "tax_hint",
        "amounts",
        "items",
        "confidence",
        "alerts",
    ],
    "properties": {
        "kind": {
            "type": "string",
            "enum": ["supplier_invoice", "supplier_credit", "other", "unknown"],
        },
        "supplier": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "tax_id", "email", "iban"],
            "properties": {
                "name": nullable("string"),
                "tax_id": nullable("string"),
                "email": nullable("string"),
                "iban": nullable("string"),
            },
        },
        "recipient_evidence": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "tax_id"],
            "properties": {
                "name": nullable("string"),
                "tax_id": nullable("string"),
            },
        },
        "reference": nullable("string"),
        "issued_on": nullable("string"),
        "due_on": nullable("string"),
        "currency_code": nullable("string"),
        "payment_reference": nullable("string"),
        "expense_class": {"type": "string", "enum": EXPENSE_CLASSES},
        "tax_hint": {"type": "string", "enum": TAX_HINTS},
        "amounts": {
            "type": "object",
            "additionalProperties": False,
            "required": ["net", "tax", "gross"],
            "properties": {
                "net": nullable("number"),
                "tax": nullable("number"),
                "gross": nullable("number"),
            },
        },
        "items": {
            "type": "array",
            "maxItems": 200,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "label",
                    "quantity",
                    "unit_price",
                    "net_amount",
                    "tax_percent",
                    "discount_percent",
                ],
                "properties": {
                    "label": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "net_amount": {"type": "number"},
                    "tax_percent": nullable("number"),
                    "discount_percent": nullable("number"),
                },
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "alerts": {
            "type": "array",
            "maxItems": 50,
            "items": {"type": "string"},
        },
    },
}


class ContractError(ValueError):
    pass


def _matches(value, expected):
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    return False


def validate_contract(value, schema=None, path="$"):
    schema = schema or DOCUMENT_RESULT_SCHEMA
    expected = schema.get("type")
    expected_types = expected if isinstance(expected, list) else [expected]
    if expected and not any(_matches(value, item) for item in expected_types):
        raise ContractError(f"{path}: invalid value type")
    if value is None:
        return value
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{path}: unsupported value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractError(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractError(f"{path}: above maximum")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise ContractError(f"{path}: missing fields {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                raise ContractError(
                    f"{path}: unexpected fields {', '.join(sorted(extras))}"
                )
        for key, child in value.items():
            if key in properties:
                validate_contract(child, properties[key], f"{path}.{key}")
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", len(value)):
            raise ContractError(f"{path}: too many items")
        item_schema = schema.get("items")
        if item_schema:
            for index, child in enumerate(value):
                validate_contract(child, item_schema, f"{path}[{index}]")
    return value


def parse_result(raw_text):
    if not isinstance(raw_text, str):
        raise ContractError("provider response is not text")
    text = raw_text.strip()
    fence = re.fullmatch(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fence:
        text = fence.group(1)
    elif text.startswith("```"):
        raise ContractError("provider response contains unsupported Markdown")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ContractError(
            f"provider response is not valid JSON at character {error.pos}"
        ) from error
    validate_contract(payload)
    return payload


_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_IDENTIFIER = re.compile(r"[^A-Z0-9]")


def clean_text(value, limit):
    if value is None:
        return None
    text = _CONTROL.sub(" ", str(value)).strip()
    return text[:limit] or None


def normalized_identifier(value):
    return _IDENTIFIER.sub("", str(value or "").upper())


def normalize_result(payload, company):
    result = json.loads(json.dumps(payload))
    for party in ("supplier", "recipient_evidence"):
        result[party] = {
            key: clean_text(value, 300) for key, value in result[party].items()
        }
    for key in (
        "reference",
        "issued_on",
        "due_on",
        "currency_code",
        "payment_reference",
    ):
        result[key] = clean_text(result[key], 300)
    for key in ("issued_on", "due_on"):
        if result[key]:
            try:
                result[key] = date.fromisoformat(result[key]).isoformat()
            except ValueError:
                result[key] = None
                result["alerts"].append(f"{key} is not a valid ISO date")
    if result["currency_code"]:
        result["currency_code"] = result["currency_code"].upper()
    result["items"] = [
        {
            **item,
            "label": clean_text(item["label"], 500) or "Imported invoice item",
        }
        for item in result["items"]
    ]
    result["alerts"] = [
        text for text in (clean_text(item, 500) for item in result["alerts"]) if text
    ]
    expected_tax_id = normalized_identifier(company.get("tax_id"))
    printed_tax_id = normalized_identifier(result["recipient_evidence"].get("tax_id"))
    recipient_matches = (
        None
        if not expected_tax_id or not printed_tax_id
        else expected_tax_id == printed_tax_id
    )
    arithmetic_ok = arithmetic_check(result)
    if recipient_matches is False:
        result["alerts"].append(
            "The printed recipient tax ID differs from the Odoo company"
        )
    elif recipient_matches is None:
        result["alerts"].append("The printed recipient tax ID could not be verified")
    if arithmetic_ok is False:
        result["alerts"].append("Printed totals do not pass the arithmetic check")
    result["alerts"] = list(dict.fromkeys(result["alerts"]))
    result["_local_checks"] = {
        "recipient_matches": recipient_matches,
        "arithmetic_ok": arithmetic_ok,
    }
    result["_company"] = {
        "name": clean_text(company.get("name"), 300),
        "tax_id": clean_text(company.get("tax_id"), 300),
        "country_code": clean_text(company.get("country_code"), 3),
        "currency_code": clean_text(company.get("currency_code"), 3),
    }
    return result


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def arithmetic_check(result):
    amounts = result["amounts"]
    net = _decimal(amounts["net"])
    tax = _decimal(amounts["tax"])
    gross = _decimal(amounts["gross"])
    checks = []
    tolerance = Decimal("0.05")
    if None not in (net, tax, gross):
        checks.append(abs(net + tax - gross) <= tolerance)
    if result["items"] and net is not None:
        item_total = sum(
            (_decimal(item["net_amount"]) or Decimal(0)) for item in result["items"]
        )
        checks.append(abs(item_total - net) <= tolerance)
    return all(checks) if checks else None
