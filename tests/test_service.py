import openai
import pytest

from sqlreviewer import service
from sqlreviewer.errors import ValidationError

from conftest import FakeClient

SQL = "SELECT * FROM fictional.orders WHERE DATE(order_date) = '2026-01-01'"


def test_merge_keeps_sources_separate(good_review):
    client = FakeClient(good_review)
    result = service.review(SQL, "PostgreSQL", client=client)
    assert result["heuristic_findings"]
    assert all(f["source"] == "heuristic" for f in result["heuristic_findings"])
    assert all(f["source"] == "ai" for f in result["ai"]["findings"])
    assert result["ai_error"] is None
    assert len(client.calls) == 1


def test_overall_risk_is_the_higher_of_the_two(good_review):
    good_review["overall_risk"] = "high"
    assert service.review("SELECT a FROM t", "PostgreSQL",
                          client=FakeClient(good_review))["overall_risk"] == "high"

    good_review["overall_risk"] = "low"
    r = service.review("DELETE FROM t", "PostgreSQL", client=FakeClient(good_review))
    assert r["heuristic_risk"] == "medium" and r["overall_risk"] == "medium"


def test_ai_failure_still_returns_heuristics():
    import httpx2 as httpx
    err = openai.RateLimitError(
        "raw", response=httpx.Response(429, request=httpx.Request("POST", "https://x.invalid")),
        body=None)
    result = service.review(SQL, "PostgreSQL", client=FakeClient(raises=err))
    assert result["ai"] is None
    assert "rate-limiting" in result["ai_error"]
    assert result["heuristic_findings"]
    assert result["ai_risk"] is None and result["overall_risk"] in ("low", "medium")


def test_malformed_ai_response_is_reported_not_raised():
    result = service.review(SQL, "PostgreSQL", client=FakeClient("garbage"))
    assert result["ai"] is None and "unexpected format" in result["ai_error"]
    assert result["heuristic_findings"]


def test_missing_api_key_reported_with_heuristics_intact():
    result = service.review(SQL, "PostgreSQL")  # no client, no key
    assert "OPENAI_API_KEY" in result["ai_error"]
    assert result["heuristic_findings"]


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_empty_sql_rejected_and_api_not_called(bad):
    client = FakeClient("{}")
    with pytest.raises(ValidationError):
        service.review(bad, "PostgreSQL", client=client)
    assert client.calls == []


def test_oversized_sql_rejected_and_api_not_called():
    client = FakeClient("{}")
    with pytest.raises(ValidationError):
        service.review("a" * 20_001, "PostgreSQL", client=client)
    assert client.calls == []


def test_bad_dialect_rejected():
    with pytest.raises(ValidationError):
        service.review("SELECT 1", "NopeSQL", client=FakeClient("{}"))
