"""Configuration read from environment variables (and a local .env file)."""

import os

from dotenv import load_dotenv

from .errors import ConfigError

DEFAULT_MODEL = "gpt-4.1-mini"
MAX_SQL_CHARS = 20_000
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 2

DIALECTS = [
    "PostgreSQL",
    "SQL Server (T-SQL)",
    "Azure Synapse",
    "MySQL",
    "Oracle",
    "SQLite",
    "Snowflake",
    "BigQuery",
    "Generic ANSI SQL",
]


def get_model() -> str:
    """Model name; override with the SQL_REVIEWER_MODEL environment variable."""
    return os.getenv("SQL_REVIEWER_MODEL", "").strip() or DEFAULT_MODEL


def get_api_key() -> str:
    """Return the API key, or raise ConfigError with a message that never contains it."""
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "OPENAI_API_KEY is not configured. Add it to the .env file in the project "
            "folder (see README), then restart the app."
        )
    return key
