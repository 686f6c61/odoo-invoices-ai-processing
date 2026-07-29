import json
import socket
import unittest

import requests

from ai_processing.core.providers import (
    EndpointPolicyError,
    ProviderError,
    ProviderGateway,
    ProviderSettings,
    _probe_code_matches,
    enforce_address_policy,
    normalize_base_url,
)


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self.payload = payload
        self.closed = False

    def iter_content(self, chunk_size):
        yield json.dumps(self.payload).encode()

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def public_resolver(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class ProviderTests(unittest.TestCase):
    def test_probe_accepts_safe_provider_wrappers(self):
        for response in (
            '{"code":"AIP-7429"}',
            '```json\n{"code":"AIP-7429"}\n```',
            '"{\\"code\\":\\"AIP-7429\\"}"',
            '{"VISION CODE":"aip_7429"}',
        ):
            self.assertTrue(_probe_code_matches(response))
        self.assertFalse(_probe_code_matches('{"code":"AIP-0000"}'))
        self.assertFalse(_probe_code_matches(None))

    def test_base_url_validation(self):
        self.assertEqual(
            normalize_base_url("https://example.com/v1/"), "https://example.com/v1"
        )
        for invalid in (
            "file:///etc/passwd",
            "https://user:pass@example.com",
            "https://example.com/v1?secret=x",
        ):
            with self.assertRaises(EndpointPolicyError):
                normalize_base_url(invalid)

    def test_private_address_is_blocked(self):
        def private_resolver(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]

        with self.assertRaises(EndpointPolicyError):
            enforce_address_policy(
                "http://localhost:11434/api", resolver=private_resolver
            )
        self.assertEqual(
            enforce_address_policy(
                "http://localhost:11434/api",
                allow_private=True,
                resolver=private_resolver,
            ),
            "http://localhost:11434/api",
        )

    def test_ollama_catalog(self):
        response = FakeResponse(
            200,
            {"models": [{"name": "vision:latest", "model": "vision:latest"}]},
        )
        session = FakeSession([response])
        gateway = ProviderGateway(session=session, resolver=public_resolver)
        result = gateway.list_models(
            ProviderSettings(
                protocol="ollama",
                base_url="https://ollama.example/api",
            )
        )
        self.assertEqual(result[0]["identifier"], "vision:latest")
        self.assertTrue(session.calls[0][1].endswith("/api/tags"))
        self.assertTrue(response.closed)

    def test_openrouter_pdf_uses_file_contract(self):
        session = FakeSession(
            [
                FakeResponse(
                    200,
                    {"choices": [{"message": {"content": '{"kind":"other"}'}}]},
                )
            ]
        )
        gateway = ProviderGateway(session=session, resolver=public_resolver)
        gateway.analyze(
            ProviderSettings(
                protocol="openrouter",
                base_url="https://openrouter.example/api/v1",
                model="model",
            ),
            filename="invoice.pdf",
            mimetype="application/pdf",
            raw=b"%PDF-test",
            system_prompt="system",
            user_prompt="user",
        )
        body = session.calls[0][2]["json"]
        parts = body["messages"][1]["content"]
        self.assertEqual(parts[1]["type"], "file")
        self.assertTrue(
            parts[1]["file"]["file_data"].startswith("data:application/pdf;base64,")
        )

    def test_openai_request_uses_generation_controls(self):
        session = FakeSession(
            [
                FakeResponse(
                    200,
                    {"output_text": '{"kind":"other"}'},
                )
            ]
        )
        gateway = ProviderGateway(session=session, resolver=public_resolver)
        gateway.analyze(
            ProviderSettings(
                protocol="openai",
                base_url="https://openai.example/v1",
                model="vision-model",
                temperature=0.2,
                max_output_tokens=1234,
            ),
            filename="invoice.png",
            mimetype="image/png",
            raw=b"\x89PNG\r\n\x1a\n",
            system_prompt="system",
            user_prompt="user",
        )
        body = session.calls[0][2]["json"]
        self.assertEqual(body["temperature"], 0.2)
        self.assertEqual(body["max_output_tokens"], 1234)
        self.assertFalse(body["store"])

    def test_authentication_error_is_not_retryable(self):
        gateway = ProviderGateway(
            session=FakeSession([FakeResponse(401, {"error": "bad key"})]),
            resolver=public_resolver,
        )
        with self.assertRaises(ProviderError) as caught:
            gateway.list_models(
                ProviderSettings(
                    protocol="ollama",
                    base_url="https://ollama.example/api",
                )
            )
        self.assertEqual(caught.exception.category, "authentication")
        self.assertFalse(caught.exception.retryable)

    def test_timeout_is_retryable(self):
        gateway = ProviderGateway(
            session=FakeSession([requests.Timeout()]),
            resolver=public_resolver,
        )
        with self.assertRaises(ProviderError) as caught:
            gateway.list_models(
                ProviderSettings(
                    protocol="ollama",
                    base_url="https://ollama.example/api",
                )
            )
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(caught.exception.category, "timeout")

    def test_redirect_is_rejected(self):
        gateway = ProviderGateway(
            session=FakeSession([FakeResponse(302, {})]),
            resolver=public_resolver,
        )
        with self.assertRaises(ProviderError) as caught:
            gateway.list_models(
                ProviderSettings(
                    protocol="ollama",
                    base_url="https://ollama.example/api",
                )
            )
        self.assertEqual(caught.exception.category, "endpoint")


if __name__ == "__main__":
    unittest.main()
