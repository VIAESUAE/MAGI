"""
Client-facing error strings: never forward raw upstream bodies (may contain key material).
Server-side, avoid logging request bodies; this module only redacts what we still return to users.
"""
from __future__ import annotations

import re
from typing import Any, Optional

# Keep messages short; long traces often duplicate vendor errors with partial tokens.
_MAX_LEN = 500

_SK = re.compile(r"sk-or-v1[a-zA-Z0-9_-]{4,200}", re.IGNORECASE)
_SKANY = re.compile(r"\b(sk-[a-zA-Z0-9_]{8,200})\b")
_BEARER = re.compile(r"Bearer\s+[A-Za-z0-9\._\-\+/=]{6,200}", re.IGNORECASE)


def redact_secrets(text: str) -> str:
    if not text:
        return ""
    s = str(text)
    s = _SK.sub("sk-or-v1[REDACTED]", s)
    s = _SKANY.sub("sk-[REDACTED]", s)
    s = _BEARER.sub("Bearer [REDACTED]", s)
    if len(s) > _MAX_LEN:
        s = s[:_MAX_LEN] + "…"
    return s


def public_error_message(exc: BaseException) -> str:
    """Safe string for JSON/SSE/NodeReport: redacted, length-capped, generic on auth noise."""
    raw = str(exc) if exc else "Unknown error"
    lower = raw.lower()
    if any(
        x in lower
        for x in (
            "authentication",
            "incorrect api key",
            "invalid api key",
            "401",
            "403",
        )
    ):
        return "The upstream model provider rejected the request. Check the API key and model id, then try again."
    return redact_secrets(raw) or "Request failed. Please try again."


def http_detail(exc: Any) -> str:
    """For HTTP 422/500 `detail` fields."""
    if exc is None:
        return "Invalid request"
    return public_error_message(exc if isinstance(exc, BaseException) else Exception(str(exc)))


def sse_error_payload(exc: BaseException) -> dict[str, str]:
    return {"event": "error", "detail": public_error_message(exc)}
