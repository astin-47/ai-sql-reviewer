import pytest

from sqlreviewer.heuristics import run_heuristics


def ids(sql):
    return {f["rule_id"] for f in run_heuristics(sql)}


@pytest.mark.parametrize("sql, rule", [
    ("SELECT * FROM t", "select-star"),
    ("select distinct a.* from a", "select-star"),
    ("DELETE FROM t", "delete-without-where"),
    ("UPDATE t SET x = 1", "update-without-where"),
    ("DROP TABLE t", "drop-statement"),
    ("TRUNCATE TABLE t", "truncate-statement"),
    ("SELECT a FROM t WHERE DATE(created) = '2026-01-01'", "function-on-column-in-where"),
    ("SELECT a FROM t WHERE name LIKE '%smith'", "leading-wildcard-like"),
    ("SELECT a FROM t WHERE a NOT IN (SELECT b FROM u)", "not-in-subquery"),
    ("SELECT a FROM t x, u y WHERE x.id = y.id", "comma-join"),
])
def test_rule_fires(sql, rule):
    assert rule in ids(sql)


@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM t",
    "SELECT a, b FROM t WHERE a = 1",
    "DELETE FROM t WHERE id = 1",
    "UPDATE t SET x = 1 WHERE id = 2",
    "SELECT a FROM t WHERE created >= '2026-01-01' AND created < '2026-01-02'",
    "SELECT a FROM t WHERE a LIKE 'abc%'",
    "SELECT a FROM t JOIN u ON t.id = u.id",
    "SELECT EXTRACT(year FROM created), a FROM t",
    "SELECT a FROM t -- SELECT * is mentioned only in a comment",
    "SELECT 'DELETE FROM t' AS note FROM t",
])
def test_no_false_positive(sql):
    assert run_heuristics(sql) == []


def test_multi_statement_delete_without_where_detected():
    assert "delete-without-where" in ids("DELETE FROM a WHERE x=1; DELETE FROM b;")


def test_findings_are_labelled_heuristic_and_hedged():
    for f in run_heuristics("SELECT * FROM t WHERE LOWER(name) = 'x'"):
        assert f["source"] == "heuristic"
        assert f["severity"] in ("info", "low", "medium")  # never an alarmist "high"
        assert any(w in f["explanation"].lower() for w in ("may", "can", "could", "depends"))
        assert f["recommendation"]
