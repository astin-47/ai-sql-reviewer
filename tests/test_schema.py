import json

import pytest

from sqlreviewer.errors import ResponseFormatError
from sqlreviewer.schema import MAX_FINDINGS, parse_review


def test_valid_response_parses_and_tags_ai(good_review):
    out = parse_review(json.dumps(good_review))
    assert out["overall_risk"] == "low"
    assert out["findings"][0]["source"] == "ai"


def test_unknown_extra_keys_are_dropped(good_review):
    good_review["evil"] = "x"
    good_review["findings"][0]["extra"] = "y"
    out = parse_review(json.dumps(good_review))
    assert "evil" not in out and "extra" not in out["findings"][0]


@pytest.mark.parametrize("raw", [None, "", "   ", "not json", "{", "[]", "42", "null", '"str"'])
def test_malformed_json_rejected(raw):
    with pytest.raises(ResponseFormatError):
        parse_review(raw)


@pytest.mark.parametrize("key", ["summary", "overall_risk", "findings", "suggested_sql", "caveats"])
def test_missing_top_level_key_rejected(good_review, key):
    del good_review[key]
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


def test_missing_finding_key_rejected(good_review):
    del good_review["findings"][0]["recommendation"]
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


@pytest.mark.parametrize("field, value", [
    ("overall_risk", "catastrophic"),
    ("summary", 5),
    ("findings", "none"),
    ("caveats", "a string"),
    ("suggested_sql", None),
])
def test_wrong_top_level_values_rejected(good_review, field, value):
    good_review[field] = value
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


@pytest.mark.parametrize("field, value", [
    ("severity", "apocalyptic"), ("category", "vibes"), ("title", 1), ("explanation", None),
])
def test_wrong_finding_values_rejected(good_review, field, value):
    good_review["findings"][0][field] = value
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


def test_non_object_finding_rejected(good_review):
    good_review["findings"] = ["oops"]
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


def test_non_string_caveat_rejected(good_review):
    good_review["caveats"] = [1]
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


def test_too_many_findings_rejected(good_review):
    good_review["findings"] = good_review["findings"] * (MAX_FINDINGS + 1)
    with pytest.raises(ResponseFormatError):
        parse_review(json.dumps(good_review))


def test_user_message_is_generic_not_internal(good_review):
    good_review["overall_risk"] = "SECRET-DETAIL"
    with pytest.raises(ResponseFormatError) as e:
        parse_review(json.dumps(good_review))
    assert "SECRET-DETAIL" not in e.value.user_message
