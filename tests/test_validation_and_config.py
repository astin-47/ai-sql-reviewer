import pytest

from sqlreviewer import config
from sqlreviewer.errors import ConfigError, ValidationError
from sqlreviewer.validation import validate_dialect, validate_sql


@pytest.mark.parametrize("bad", ["", "   ", "\n\t "])
def test_empty_sql_rejected(bad):
    with pytest.raises(ValidationError):
        validate_sql(bad)


@pytest.mark.parametrize("bad", [None, 123, ["SELECT 1"]])
def test_non_string_rejected(bad):
    with pytest.raises(ValidationError):
        validate_sql(bad)


def test_null_byte_rejected():
    with pytest.raises(ValidationError):
        validate_sql("SELECT 1\x00")


def test_length_limit_boundaries():
    assert validate_sql("a" * config.MAX_SQL_CHARS) == "a" * config.MAX_SQL_CHARS
    with pytest.raises(ValidationError, match="too long"):
        validate_sql("a" * (config.MAX_SQL_CHARS + 1))


def test_sql_is_stripped():
    assert validate_sql("  SELECT 1  \n") == "SELECT 1"


def test_dialect_validation():
    assert validate_dialect("PostgreSQL") == "PostgreSQL"
    with pytest.raises(ValidationError):
        validate_dialect("KlingonSQL")


def test_missing_api_key_raises_config_error():
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        config.get_api_key()


def test_blank_api_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    with pytest.raises(ConfigError):
        config.get_api_key()


def test_api_key_read_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")
    assert config.get_api_key() == "sk-test-not-real"


def test_model_default_and_override(monkeypatch):
    assert config.get_model() == config.DEFAULT_MODEL
    monkeypatch.setenv("SQL_REVIEWER_MODEL", "some-model")
    assert config.get_model() == "some-model"
