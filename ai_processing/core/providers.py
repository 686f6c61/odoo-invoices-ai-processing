import base64
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

from .contracts import DOCUMENT_RESULT_SCHEMA
from .document_io import capability_probe_image

MAX_RESPONSE_BYTES = 1_000_000
MAX_SAFE_ERROR = 320
PROBE_CODE_PATTERN = re.compile(r"\bAIP[\s_-]*7429\b", re.IGNORECASE)


class EndpointPolicyError(ValueError):
    pass


class ProviderError(RuntimeError):
    def __init__(self, message, *, category="provider", retryable=False):
        safe_text = str(message or "AI provider failure").replace("\x00", " ")
        RuntimeError.__init__(self, safe_text[:MAX_SAFE_ERROR])
        self.classification = str(category or "provider")
        self.can_retry = bool(retryable)

    @property
    def category(self):
        return self.classification

    @property
    def retryable(self):
        return self.can_retry


@dataclass(frozen=True)
class ProviderSettings:
    protocol: str
    base_url: str
    model: str = ""
    api_key: str = ""
    timeout: int = 90
    temperature: float = 0
    max_output_tokens: int = 4000
    allow_private: bool = False
    structured_mode: str = "schema"
    pdf_engine: str = "auto"
    pdf_detail: str = "auto"


def normalize_base_url(candidate):
    address = str(candidate or "").strip()
    while address.endswith("/"):
        address = address[:-1]
    components = urlsplit(address)
    if components.scheme.lower() not in ("http", "https") or not components.hostname:
        raise EndpointPolicyError("The service URL must be a valid HTTP or HTTPS URL")
    forbidden_parts = (
        components.username,
        components.password,
        components.query,
        components.fragment,
    )
    if any(forbidden_parts):
        raise EndpointPolicyError(
            "The service URL cannot contain credentials, query parameters or fragments"
        )
    return address


def enforce_address_policy(base_url, *, allow_private=False, resolver=None):
    normalized = normalize_base_url(base_url)
    if allow_private:
        return normalized
    components = urlsplit(normalized)
    lookup = resolver if resolver is not None else socket.getaddrinfo
    service_port = components.port
    if service_port is None:
        service_port = 443 if components.scheme.lower() == "https" else 80
    try:
        answers = lookup(
            components.hostname, service_port, type=socket.SOCK_STREAM
        )
    except OSError as error:
        message = "The service hostname could not be resolved"
        raise EndpointPolicyError(message) from error
    unique_addresses = {answer[4][0] for answer in answers if answer[4]}
    if not unique_addresses:
        raise EndpointPolicyError("The service hostname resolved to no address")
    for raw_address in unique_addresses:
        try:
            parsed_address = ipaddress.ip_address(raw_address)
        except ValueError as error:
            message = "The service returned an invalid network address"
            raise EndpointPolicyError(message) from error
        if not parsed_address.is_global:
            raise EndpointPolicyError(
                "Private, loopback and link-local services require explicit approval"
            )
    return normalized


def _data_uri(mimetype, raw):
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mimetype};base64,{encoded}"


def _headers(settings):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    return headers


def _response_format(settings, schema):
    if settings.structured_mode == "json":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "supplier_document",
            "strict": True,
            "schema": schema,
        },
    }


def _probe_code_matches(text):
    """Accept harmless provider wrappers while requiring the unseen image code."""
    return isinstance(text, str) and bool(PROBE_CODE_PATTERN.search(text))


class ProviderGateway:
    def __init__(self, session=None, resolver=None):
        self._http = session if session is not None else requests.Session()
        self._dns_lookup = resolver

    def list_models(self, settings):
        base = self._safe_base(settings)
        payload = self._get(
            f"{base}/tags" if settings.protocol == "ollama" else f"{base}/models",
            settings,
        )
        if settings.protocol == "ollama":
            values = payload.get("models")
            if not isinstance(values, list):
                raise ProviderError("The Ollama catalog has an invalid shape")
            return [
                {
                    "identifier": str(
                        item.get("model") or item.get("name") or ""
                    ).strip(),
                    "label": str(item.get("name") or item.get("model") or "").strip(),
                    "context_length": 0,
                    "modalities": "",
                    "declared_document_capable": False,
                }
                for item in values
                if item.get("model") or item.get("name")
            ]
        values = payload.get("data")
        if not isinstance(values, list):
            raise ProviderError("The model catalog has an invalid shape")
        result = []
        for item in values:
            identifier = str(item.get("id") or "").strip()
            if not identifier:
                continue
            architecture = item.get("architecture") or {}
            input_modalities = (
                architecture.get("input_modalities")
                or item.get("input_modalities")
                or []
            )
            if isinstance(input_modalities, str):
                input_modalities = [input_modalities]
            modalities = ",".join(str(value) for value in input_modalities)
            declared = any(
                value.lower() in {"image", "file", "pdf", "document", "vision"}
                for value in map(str, input_modalities)
            )
            result.append(
                {
                    "identifier": identifier,
                    "label": str(item.get("name") or identifier),
                    "context_length": int(item.get("context_length") or 0),
                    "modalities": modalities,
                    "declared_document_capable": declared,
                }
            )
        return result

    def analyze(
        self,
        settings,
        *,
        filename,
        mimetype,
        raw,
        system_prompt,
        user_prompt,
        rendered_pages=None,
    ):
        base = self._safe_base(settings)
        if settings.protocol == "openai":
            body = self._openai_body(
                settings,
                filename,
                mimetype,
                raw,
                system_prompt,
                user_prompt,
            )
            payload = self._post(f"{base}/responses", settings, body)
            return self._openai_text(payload)
        if settings.protocol == "openrouter":
            body = self._openrouter_body(
                settings,
                filename,
                mimetype,
                raw,
                system_prompt,
                user_prompt,
            )
            payload = self._post(f"{base}/chat/completions", settings, body)
            return self._chat_text(payload)
        if settings.protocol == "ollama":
            body = self._ollama_body(
                settings,
                mimetype,
                raw,
                system_prompt,
                user_prompt,
                rendered_pages,
            )
            payload = self._post(f"{base}/chat", settings, body)
            message = payload.get("message") or {}
            content = message.get("content")
            if not isinstance(content, str):
                raise ProviderError("Ollama returned no text response", retryable=True)
            return content
        body = self._compatible_body(
            settings,
            mimetype,
            raw,
            system_prompt,
            user_prompt,
            rendered_pages,
        )
        payload = self._post(f"{base}/chat/completions", settings, body)
        return self._chat_text(payload)

    def probe_document_capability(self, settings):
        probe_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["code"],
            "properties": {"code": {"type": "string"}},
        }
        raw = capability_probe_image()
        base = self._safe_base(settings)
        system_prompt = "Read the image. Return only the required JSON object."
        user_prompt = "Return the exact value printed after VISION CODE."
        if settings.protocol == "openai":
            body = self._openai_body(
                settings,
                "capability.png",
                "image/png",
                raw,
                system_prompt,
                user_prompt,
                schema=probe_schema,
            )
            payload = self._post(f"{base}/responses", settings, body)
            text = self._openai_text(payload)
        elif settings.protocol == "ollama":
            body = {
                "model": settings.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_prompt,
                        "images": [base64.b64encode(raw).decode("ascii")],
                    },
                ],
                "format": "json"
                if settings.structured_mode == "json"
                else probe_schema,
                "options": {"temperature": 0},
            }
            payload = self._post(f"{base}/chat", settings, body)
            text = (payload.get("message") or {}).get("content", "")
        else:
            body = {
                "model": settings.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": _data_uri("image/png", raw)},
                            },
                        ],
                    },
                ],
                "temperature": 0,
                "response_format": _response_format(settings, probe_schema),
            }
            payload = self._post(f"{base}/chat/completions", settings, body)
            text = self._chat_text(payload)
        if not isinstance(text, str):
            raise ProviderError(
                "The model did not complete the document capability probe"
            )
        return _probe_code_matches(text)

    def _safe_base(self, settings):
        return enforce_address_policy(
            settings.base_url,
            allow_private=settings.allow_private,
            resolver=self._dns_lookup,
        )

    def _openai_body(
        self,
        settings,
        filename,
        mimetype,
        raw,
        system_prompt,
        user_prompt,
        *,
        schema=None,
    ):
        if mimetype == "application/pdf":
            document = {
                "type": "input_file",
                "filename": filename,
                "file_data": _data_uri(mimetype, raw),
                "detail": settings.pdf_detail,
            }
        else:
            document = {
                "type": "input_image",
                "image_url": _data_uri(mimetype, raw),
                "detail": "high",
            }
        format_value = (
            {"type": "json_object"}
            if settings.structured_mode == "json"
            else {
                "type": "json_schema",
                "name": "supplier_document",
                "strict": True,
                "schema": schema or DOCUMENT_RESULT_SCHEMA,
            }
        )
        return {
            "model": settings.model,
            "instructions": system_prompt,
            "input": [
                {
                    "role": "user",
                    "content": [
                        document,
                        {"type": "input_text", "text": user_prompt},
                    ],
                }
            ],
            "text": {"format": format_value},
            "temperature": settings.temperature,
            "max_output_tokens": settings.max_output_tokens,
            "store": False,
        }

    def _openrouter_body(
        self,
        settings,
        filename,
        mimetype,
        raw,
        system_prompt,
        user_prompt,
    ):
        content = [{"type": "text", "text": user_prompt}]
        if mimetype == "application/pdf":
            content.append(
                {
                    "type": "file",
                    "file": {
                        "filename": filename,
                        "file_data": _data_uri(mimetype, raw),
                    },
                }
            )
        else:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _data_uri(mimetype, raw)},
                }
            )
        body = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_output_tokens,
            "response_format": _response_format(settings, DOCUMENT_RESULT_SCHEMA),
        }
        if mimetype == "application/pdf" and settings.pdf_engine != "auto":
            body["plugins"] = [
                {
                    "id": "file-parser",
                    "pdf": {"engine": settings.pdf_engine},
                }
            ]
        return body

    def _compatible_body(
        self,
        settings,
        mimetype,
        raw,
        system_prompt,
        user_prompt,
        rendered_pages,
    ):
        content = [{"type": "text", "text": user_prompt}]
        images = rendered_pages if mimetype == "application/pdf" else [raw]
        image_type = "image/jpeg" if mimetype == "application/pdf" else mimetype
        for image in images or []:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _data_uri(image_type, image)},
                }
            )
        return {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_output_tokens,
            "response_format": _response_format(settings, DOCUMENT_RESULT_SCHEMA),
        }

    def _ollama_body(
        self,
        settings,
        mimetype,
        raw,
        system_prompt,
        user_prompt,
        rendered_pages,
    ):
        images = rendered_pages if mimetype == "application/pdf" else [raw]
        return {
            "model": settings.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [
                        base64.b64encode(image).decode("ascii")
                        for image in images or []
                    ],
                },
            ],
            "format": (
                "json" if settings.structured_mode == "json" else DOCUMENT_RESULT_SCHEMA
            ),
            "options": {
                "temperature": settings.temperature,
                "num_predict": settings.max_output_tokens,
            },
        }

    def _get(self, url, settings):
        return self._request("GET", url, settings)

    def _post(self, url, settings, body):
        return self._request("POST", url, settings, body)

    def _request(self, method, url, settings, body=None):
        try:
            response = self._http.request(
                method,
                url,
                headers=_headers(settings),
                json=body,
                timeout=(10, settings.timeout),
                allow_redirects=False,
                stream=True,
            )
        except requests.Timeout as error:
            raise ProviderError(
                "The AI service timed out", category="timeout", retryable=True
            ) from error
        except requests.RequestException as error:
            raise ProviderError(
                "The AI service could not be reached",
                category="network",
                retryable=True,
            ) from error
        try:
            if 300 <= response.status_code < 400:
                raise ProviderError(
                    "AI service redirects are not allowed", category="endpoint"
                )
            if response.status_code in {401, 403}:
                raise ProviderError(
                    "The AI service rejected the credentials",
                    category="authentication",
                )
            if response.status_code == 429:
                raise ProviderError(
                    "The AI service rate limit was reached",
                    category="rate_limit",
                    retryable=True,
                )
            if response.status_code >= 500:
                raise ProviderError(
                    "The AI service is temporarily unavailable",
                    category="provider",
                    retryable=True,
                )
            if response.status_code >= 400:
                raise ProviderError(
                    f"The AI service rejected the request (HTTP {response.status_code})",
                    category="request",
                )
            chunks = []
            size = 0
            try:
                for chunk in response.iter_content(chunk_size=65536):
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise ProviderError(
                            "The AI service response is too large",
                            category="response",
                        )
                    chunks.append(chunk)
                return json.loads(b"".join(chunks).decode("utf-8"))
            except requests.RequestException as error:
                raise ProviderError(
                    "The AI service response was interrupted",
                    category="network",
                    retryable=True,
                ) from error
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ProviderError(
                    "The AI service returned invalid JSON",
                    category="response",
                    retryable=True,
                ) from error
        finally:
            close = getattr(response, "close", None)
            if close:
                close()

    @staticmethod
    def _chat_text(payload):
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError("The AI service returned no completion", retryable=True)
        content = (choices[0].get("message") or {}).get("content")
        if not isinstance(content, str):
            raise ProviderError(
                "The AI service returned no text completion", retryable=True
            )
        return content

    @staticmethod
    def _openai_text(payload):
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct:
            return direct
        pieces = []
        for item in payload.get("output") or []:
            for content in item.get("content") or []:
                text = content.get("text")
                if content.get("type") in {"output_text", "text"} and isinstance(
                    text, str
                ):
                    pieces.append(text)
        if not pieces:
            raise ProviderError("OpenAI returned no output text", retryable=True)
        return "".join(pieces)
