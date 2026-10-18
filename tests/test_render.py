from ui import render


def test_finding_card_escapes_untrusted_html():
    card = render.finding_card({
        "source": "ai", "category": "security", "severity": "high",
        "title": "<script>alert(1)</script>", "explanation": "<img src=x onerror=1>",
        "recommendation": "a & b",
    })
    assert "<script>" not in card and "<img" not in card
    assert "&lt;script&gt;" in card and "a &amp; b" in card
    assert "sev-high" in card and "AI-generated" in card


def test_unknown_severity_and_risk_fall_back_safely():
    card = render.finding_card({"source": "heuristic", "category": "x", "severity": '"><b>',
                                "title": "t", "explanation": "e", "recommendation": "r"})
    assert "sev-info" in card and "<b>" not in card.split("<h3>")[0]
    assert "risk-medium" in render.risk_block("bogus", "n")


def test_empty_and_caveats_rendering():
    assert "Nothing" in render.findings_html([], "Nothing here")
    assert "&lt;i&gt;" in render.caveats_html(["<i>x</i>"])
