"""Input validation. Pure functions, no I/O."""

from .config import DIALECTS, MAX_SQL_CHARS
from .errors import ValidationError


def validate_sql(sql) -> str:
    """Return the SQL with surrounding whitespace removed, or raise ValidationError."""
    if not isinstance(sql, str):
        raise ValidationError("The SQL input must be text.")
    if "\x00" in sql:
        raise ValidationError("The SQL input contains unsupported control characters.")
    cleaned = sql.strip()
    if not cleaned:
        raise ValidationError("Please paste a SQL query to review.")
    if len(cleaned) > MAX_SQL_CHARS:
        raise ValidationError(
            f"The SQL is too long ({len(cleaned):,} characters). "
            f"The maximum is {MAX_SQL_CHARS:,}."
        )
    return cleaned


def validate_dialect(dialect) -> str:
    if dialect not in DIALECTS:
        raise ValidationError("Please choose a SQL dialect from the list.")
    return dialect
