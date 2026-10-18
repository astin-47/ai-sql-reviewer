# AI SQL Reviewer

A Streamlit app that reviews SQL with the OpenAI Responses API and a small set of local, deterministic checks.
It returns structured findings (category, severity, explanation, recommendation), an overall risk rating, a suggested rewrite and caveats.

> **AI recommendations require human review.** Suggestions can be wrong, incomplete or not actually faster. Always test against your own data and execution plans.
> Submitted SQL is analysed **as text only and is never executed**.

## Setup (Windows PowerShell)

```powershell
cd D:\Projects\ai-sql-reviewer
python -m venv .venv                 # skip if .venv already exists
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project folder (it is git-ignored) containing one line:

```
OPENAI_API_KEY=your-key-here
```

Optional: `SQL_REVIEWER_MODEL=gpt-4.1-mini` (the default) to use another model.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501 if the browser does not open automatically. Use the "Load an example" dropdown to try the fictional queries in `examples/`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Tests use mocked API clients, block network access, ignore your real `.env`, and cost no API credits.
(`test_api.py` and `test_reviewer.py` in the project root are older manual scripts that call the real API; run them by hand only if you want a live check.)

## Architecture

```
app.py                 Streamlit UI only
sqlreviewer/
  config.py            env vars, limits, dialect list
  validation.py        input checks (empty, type, length, control chars)
  heuristics.py        local regex rules -> findings tagged source="heuristic"
  schema.py            JSON schema sent to the API + strict validation of the reply
  ai_client.py         the only module that calls OpenAI; maps errors to safe messages
  service.py           validate -> heuristics -> AI -> combined result
  errors.py            exceptions carrying user-safe messages
tests/                 pytest suite (mocked)
examples/              fictional-schema SQL samples
```

Flow: `app.py` calls `service.review()`. Heuristic findings and AI findings stay in separate lists and are shown in separate, labelled sections. If the AI step fails (rate limit, missing key, malformed reply), the heuristic results are still shown with a plain error message.

## Safety design

- SQL is never executed, only sent as quoted text to the model, with instructions to treat it as untrusted.
- SQL is not logged; only exception type names are logged on failures.
- The API key is read from the environment/`.env` only, and error messages never include it or raw exception text.
- The AI reply is validated against the schema; wrong types, bad enums, missing keys or oversized output are rejected and unknown keys dropped.

## Limitations

- Heuristics are regex-based text matches, not a SQL parser. They are intentionally conservative and worded as hints, and can miss things or occasionally flag harmless code.
- The AI sees only the SQL you paste: no schema, indexes, row counts or query plans. Performance remarks are hypotheses.
- A suggested rewrite is not guaranteed to be equivalent or faster.
- Pasted SQL is sent to OpenAI. Don't include secrets or sensitive data.
- Input limit: 20,000 characters.
