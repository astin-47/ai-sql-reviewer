import json
import socket

import pytest

GOOD_REVIEW = {
    "summary": "Looks mostly fine.",
    "overall_risk": "low",
    "findings": [{
        "category": "performance", "severity": "low", "title": "Possible scan",
        "explanation": "Might scan.", "recommendation": "Check the plan.",
    }],
    "suggested_sql": "SELECT 1;",
    "caveats": ["No schema supplied."],
}


class FakeResponse:
    def __init__(self, output_text, status="completed"):
        self.output_text = output_text
        self.status = status


class FakeClient:
    """Stands in for openai.OpenAI. Records calls; returns or raises what it is given."""

    def __init__(self, output=None, raises=None):
        self.calls = []
        self._output, self._raises = output, raises
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._raises:
            raise self._raises
        out = self._output
        return out if isinstance(out, FakeResponse) else FakeResponse(
            out if isinstance(out, str) else json.dumps(out))


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    """No network, no real .env, no real key in any test."""
    def no_network(*a, **k):
        raise AssertionError("Network access attempted in a unit test")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr("sqlreviewer.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SQL_REVIEWER_MODEL", raising=False)


@pytest.fixture
def good_review():
    return json.loads(json.dumps(GOOD_REVIEW))
