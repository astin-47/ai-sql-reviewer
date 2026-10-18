"""The expected AI response shape, and strict validation of what comes back."""

import json

from .errors import ResponseFormatError

CATEGORIES = ["correctness", "performance", "readability", "maintainability", "security"]
SEVERITIES = ["info", "low", "medium", "high"]
RISKS = ["low", "medium", "high"]
MAX_FINDINGS = 50
MAX_TEXT_CHARS = 8_000
MAX_SQL_OUT_CHARS = 40_000
SOURCE = "ai"

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "overall_risk": {"type": "string", "enum": RISKS},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": CATEGORIES},
                    "severity": {"type": "string", "enum": SEVERITIES},
                    "title": {"type": "string"},
                    "explanation": {"type": "string"},
                    "recommendation": {"type": "string"},
                },
                "required": ["category", "severity", "title", "explanation", "recommendation"],
                "additionalProperties": False,
            },
        },
        "suggested_sql": {"type": "string"},
        "caveats": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "overall_risk", "findings", "suggested_sql", "caveats"],
    "additionalProperties": False,
}


def _bad(reason: str) -> ResponseFormatError:
    # The reason is for developers/tests; the user-facing message stays generic.
    err = ResponseFormatError(
        "The AI service returned a response in an unexpected format. "
        "Please try again; if it keeps happening, try a shorter query."
    )
    err.reason = reason
    return err


def _text(value, name: str, limit: int = MAX_TEXT_CHARS) -> str:
    if not isinstance(value, str):
        raise _bad(f"{name} is not a string")
    if len(value) > limit:
        raise _bad(f"{name} is too long")
    return value


def _choice(value, name: str, allowed: list[str]) -> str:
    if value not in allowed:
        raise _bad(f"{name} is not one of the allowed values")
    return value


def parse_review(raw_text) -> dict:
    """Parse and validate the model's JSON. Returns a normalised dict or raises
    ResponseFormatError. Unknown extra keys are dropped, never passed on."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise _bad("empty response")
    try:
        data = json.loads(raw_text)
    except (ValueError, RecursionError):
        raise _bad("not valid JSON") from None
    if not isinstance(data, dict):
        raise _bad("top level is not an object")

    missing = [k for k in REVIEW_SCHEMA["required"] if k not in data]
    if missing:
        raise _bad(f"missing keys: {', '.join(missing)}")

    raw_findings = data["findings"]
    if not isinstance(raw_findings, list) or len(raw_findings) > MAX_FINDINGS:
        raise _bad("findings is not a reasonably sized list")

    findings = []
    for i, item in enumerate(raw_findings):
        if not isinstance(item, dict):
            raise _bad(f"finding {i} is not an object")
        absent = [k for k in REVIEW_SCHEMA["properties"]["findings"]["items"]["required"]
                  if k not in item]
        if absent:
            raise _bad(f"finding {i} is missing keys")
        findings.append({
            "source": SOURCE,
            "category": _choice(item["category"], "category", CATEGORIES),
            "severity": _choice(item["severity"], "severity", SEVERITIES),
            "title": _text(item["title"], "title", 300),
            "explanation": _text(item["explanation"], "explanation"),
            "recommendation": _text(item["recommendation"], "recommendation"),
        })

    caveats = data["caveats"]
    if not isinstance(caveats, list) or len(caveats) > MAX_FINDINGS:
        raise _bad("caveats is not a reasonably sized list")

    return {
        "summary": _text(data["summary"], "summary"),
        "overall_risk": _choice(data["overall_risk"], "overall_risk", RISKS),
        "findings": findings,
        "suggested_sql": _text(data["suggested_sql"], "suggested_sql", MAX_SQL_OUT_CHARS),
        "caveats": [_text(c, "caveat") for c in caveats],
    }
