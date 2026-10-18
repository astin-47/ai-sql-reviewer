"""Small deterministic checks that run locally, with no network and no SQL execution.

These are *pattern matches on text*, not a SQL parser. Every rule is deliberately
conservative and worded as "may"/"could": a match is a prompt for human review, never
a proof of a defect. Severities are therefore low ("info"/"low"/"medium").
"""

import re

SOURCE = "heuristic"


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def _strip_literals(sql: str) -> str:
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def _statements(sql: str) -> list[str]:
    return [s.strip() for s in sql.split(";") if s.strip()]


def _finding(rule_id, category, severity, title, explanation, recommendation):
    return {
        "rule_id": rule_id,
        "source": SOURCE,
        "category": category,
        "severity": severity,
        "title": title,
        "explanation": explanation,
        "recommendation": recommendation,
    }


_SELECT_STAR = re.compile(
    r"\bselect\s+(?:distinct\s+)?(?:top\s*\(?\s*\d+\s*\)?\s+)?(?:[\w\[\]\"`]+\.)?\*"
)
_FUNC_ON_COLUMN = re.compile(
    r"\b(?:date|cast|lower|upper|year|month|day|convert|trunc|datepart|to_char|"
    r"coalesce|isnull)\s*\(\s*[a-z_][\w.]*"
)
_WHERE_CLAUSE = re.compile(
    r"\bwhere\b(.*?)(?=\bgroup\s+by\b|\border\s+by\b|\bhaving\b|\bunion\b|$)", re.S
)
_LEADING_WILDCARD = re.compile(r"\bi?like\s+n?'%", re.I)
_NOT_IN_SUBQUERY = re.compile(r"\bnot\s+in\s*\(\s*select\b")
_COMMA_JOIN = re.compile(r"\bfrom\s+[\w.\[\]\"`]+(?:\s+(?:as\s+)?\w+)?\s*,\s*[\w.\[\]\"`]+")
_DESTRUCTIVE = re.compile(r"^(?:drop|truncate)\b")


def run_heuristics(sql: str) -> list[dict]:
    """Return heuristic findings for the SQL text (possibly empty)."""
    with_literals = _strip_comments(sql)
    code = _strip_literals(with_literals).lower()
    findings: list[dict] = []

    if _SELECT_STAR.search(code):
        findings.append(_finding(
            "select-star", "maintainability", "info", "SELECT * used",
            "Selecting every column may return more data than needed and can make the "
            "query's output change if the table's columns change. Whether this matters "
            "depends on the table width and how the result is used.",
            "Consider listing only the columns the consumer needs.",
        ))

    for stmt in _statements(code):
        if re.match(r"^(?:delete|update)\b", stmt) and not re.search(r"\bwhere\b", stmt):
            verb = stmt.split()[0].upper()
            findings.append(_finding(
                f"{verb.lower()}-without-where", "correctness", "medium",
                f"{verb} statement has no WHERE clause",
                f"A {verb} without a WHERE clause may affect every row in the table. "
                "That can be intentional (for example, in a staging table), so this is "
                "a prompt to double-check, not necessarily an error.",
                "Confirm that touching all rows is intended; otherwise add a WHERE "
                "clause, and consider running it in a transaction you can roll back.",
            ))
        if _DESTRUCTIVE.match(stmt):
            verb = stmt.split()[0].upper()
            findings.append(_finding(
                f"{verb.lower()}-statement", "security", "medium",
                f"{verb} statement present",
                f"{verb} permanently removes objects or data and is often hard to undo. "
                "It may be appropriate in a migration or cleanup script.",
                "Verify the target object and environment, and make sure a backup or "
                "rollback path exists before running it anywhere.",
            ))

    where = _WHERE_CLAUSE.search(code)
    if where and _FUNC_ON_COLUMN.search(where.group(1)):
        findings.append(_finding(
            "function-on-column-in-where", "performance", "low",
            "Function applied to a column in WHERE",
            "Wrapping a column in a function inside a filter can prevent some engines "
            "from using an index on that column. Whether it actually affects "
            "performance depends on the engine, available indexes and data volume, "
            "which this check cannot see.",
            "If this query is slow, test a version that compares the bare column "
            "(for example, a range filter) and compare execution plans.",
        ))

    if _LEADING_WILDCARD.search(with_literals.lower()):
        findings.append(_finding(
            "leading-wildcard-like", "performance", "info",
            "LIKE pattern starts with a wildcard",
            "A pattern beginning with % generally cannot use a standard B-tree index "
            "seek, so it may scan more rows. This may be unavoidable for substring "
            "search and is harmless on small tables.",
            "If this is a hot path on a large table, consider full-text search or "
            "another indexing approach appropriate for your engine.",
        ))

    if _NOT_IN_SUBQUERY.search(code):
        findings.append(_finding(
            "not-in-subquery", "correctness", "low",
            "NOT IN with a subquery",
            "If the subquery can return NULL, NOT IN may return no rows at all, "
            "which is a common source of surprising results. If the column is "
            "declared NOT NULL this concern does not apply.",
            "Consider NOT EXISTS, or filter NULLs out of the subquery explicitly.",
        ))

    if _COMMA_JOIN.search(code):
        findings.append(_finding(
            "comma-join", "readability", "info",
            "Comma-separated tables in FROM",
            "Old-style comma joins put the join condition in WHERE; if a condition "
            "is missing the result may silently become a cross join. This query may "
            "well be correct as written.",
            "Consider explicit JOIN ... ON syntax so join conditions are easy to "
            "spot and review.",
        ))

    return findings
