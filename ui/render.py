"""HTML fragments for the UI. Every dynamic string is escaped: AI output is untrusted."""

from html import escape

_SOURCE_LABEL = {"heuristic": "Heuristic check", "ai": "AI-generated"}


def _e(value) -> str:
    return escape(str(value), quote=True)


def finding_card(finding: dict) -> str:
    sev = finding["severity"] if finding["severity"] in ("info", "low", "medium", "high") else "info"
    source = _SOURCE_LABEL.get(finding.get("source"), "Finding")
    return (
        f'<article class="finding sev-{sev}">'
        f'<p class="meta"><span class="chip"></span>{_e(sev.title())} severity '
        f'· {_e(str(finding["category"]).title())} · {_e(source)}</p>'
        f'<h3>{_e(finding["title"])}</h3>'
        f'<p><b>Why it may matter.</b> {_e(finding["explanation"])}</p>'
        f'<p><b>What to consider.</b> {_e(finding["recommendation"])}</p>'
        f'</article>'
    )


def findings_html(findings: list[dict], empty_message: str) -> str:
    if not findings:
        return f'<p class="empty">{_e(empty_message)}</p>'
    return "".join(finding_card(f) for f in findings)


def risk_block(risk: str, note: str) -> str:
    risk = risk if risk in ("low", "medium", "high") else "medium"
    return (
        f'<section class="verdict risk-{risk}">'
        f'<h2>{_e(risk.title())} risk</h2><p>{_e(note)}</p></section>'
    )


def section_head(title: str, note: str, kind: str) -> str:
    return (
        f'<div class="section-head {kind}"><h2>{_e(title)}</h2>'
        f'<p>{_e(note)}</p></div>'
    )


def caveats_html(caveats: list[str]) -> str:
    items = "".join(f"<li>{_e(c)}</li>" for c in caveats)
    return f'<ul class="caveats">{items}</ul>'
