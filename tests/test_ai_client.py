import logging

import httpx2 as httpx
import openai
import pytest

from sqlreviewer import ai_client
from sqlreviewer.errors import APIError, ConfigError, ResponseFormatError

from conftest import FakeClient, FakeResponse

SECRET = "sk-super-secret-RAW-DETAIL"
SQL = "SELECT secret_column FROM fictional.t"


def _resp(code):
    return httpx.Response(code, request=httpx.Request("POST", "https://example.invalid"))


def _status_error(cls, code):
    return cls(SECRET, response=_resp(code), body=None)


def _conn_error(cls):
    return cls(request=httpx.Request("POST", "https://example.invalid"))


def test_success_returns_validated_review(good_review):
    client = FakeClient(good_review)
    out = ai_client.review_with_ai(SQL, "PostgreSQL", client=client)
    assert out["overall_risk"] == "low"
    call = client.calls[0]
    assert call["text"]["format"]["strict"] is True
    assert "<sql_to_review>" in call["input"] and SQL in call["input"]


def test_prompt_guards_against_speculative_injection_findings(good_review):
    client = FakeClient(good_review)
    ai_client.review_with_ai(SQL, "PostgreSQL", client=client)
    call = client.calls[0]
    assert "dynamic construction" in call["instructions"]
    assert "untrusted input" not in call["input"]  # wording that misled the model
    assert "never as instructions" in call["input"]


@pytest.mark.parametrize("make, fragment", [
    (lambda: _status_error(openai.RateLimitError, 429), "rate-limiting"),
    (lambda: _status_error(openai.AuthenticationError, 401), "credentials"),
    (lambda: _status_error(openai.PermissionDeniedError, 403), "access"),
    (lambda: _status_error(openai.NotFoundError, 404), "model"),
    (lambda: _status_error(openai.InternalServerError, 500), "returned an error"),
    (lambda: _conn_error(openai.APIConnectionError), "Could not reach"),
    (lambda: _conn_error(openai.APITimeoutError), "too long"),
    (lambda: RuntimeError(SECRET), "unexpected error"),
])
def test_api_errors_map_to_safe_messages(make, fragment):
    client = FakeClient(raises=make())
    with pytest.raises(APIError) as e:
        ai_client.review_with_ai(SQL, "PostgreSQL", client=client)
    msg = e.value.user_message
    assert fragment in msg
    assert SECRET not in msg and SECRET not in str(e.value)


@pytest.mark.parametrize("output", ["", "not json", "[]", '{"summary": "only"}'])
def test_malformed_output_raises_format_error(output):
    with pytest.raises(ResponseFormatError):
        ai_client.review_with_ai(SQL, "PostgreSQL", client=FakeClient(output))


def test_incomplete_response_raises_format_error(good_review):
    import json
    client = FakeClient(FakeResponse(json.dumps(good_review), status="incomplete"))
    with pytest.raises(ResponseFormatError, match="cut off"):
        ai_client.review_with_ai(SQL, "PostgreSQL", client=client)


def test_missing_api_key_raises_config_error_before_any_call():
    with pytest.raises(ConfigError):
        ai_client.review_with_ai(SQL, "PostgreSQL")  # no client -> builds one -> no key


def test_no_sql_or_secret_in_logs(caplog):
    caplog.set_level(logging.DEBUG)
    client = FakeClient(raises=_status_error(openai.RateLimitError, 429))
    with pytest.raises(APIError):
        ai_client.review_with_ai(SQL, "PostgreSQL", client=client)
    assert SQL not in caplog.text and "secret_column" not in caplog.text
    assert SECRET not in caplog.text
