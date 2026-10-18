"""Orchestration: validate -> local heuristics -> AI review -> combined result.

Heuristic and AI findings are kept in separate lists and never mixed. If the AI step
fails, the heuristic results are still returned together with a safe error message.
"""

from . import ai_client
from .errors import ReviewError
from .heuristics import run_heuristics
from .validation import validate_dialect, validate_sql

_RANK = {"low": 0, "medium": 1, "high": 2}


def _heuristic_risk(findings: list[dict]) -> str:
    return "medium" if any(f["severity"] in ("medium", "high") for f in findings) else "low"


def review(sql, dialect: str, client=None) -> dict:
    """Review SQL. Raises ValidationError for bad input; AI failures are returned in
    `ai_error` rather than raised, so heuristic results are never lost."""
    clean = validate_sql(sql)
    dialect = validate_dialect(dialect)

    heuristic_findings = run_heuristics(clean)
    heuristic_risk = _heuristic_risk(heuristic_findings)

    ai = None
    ai_error = None
    try:
        ai = ai_client.review_with_ai(clean, dialect, client=client)
    except ReviewError as exc:
        ai_error = exc.user_message

    ai_risk = ai["overall_risk"] if ai else None
    overall = max(filter(None, [heuristic_risk, ai_risk]), key=_RANK.__getitem__)

    return {
        "dialect": dialect,
        "heuristic_findings": heuristic_findings,
        "heuristic_risk": heuristic_risk,
        "ai": ai,
        "ai_risk": ai_risk,
        "ai_error": ai_error,
        "overall_risk": overall,
    }
