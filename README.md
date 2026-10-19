# Job_Match_Agent

**Status: Week 1 complete and validated.**

An agentic AI system that matches a candidate's CV against AI/ML job postings
in Germany, explains *why* a job fits or doesn't, and ranks recommendations.
The project is built incrementally so deterministic logic, LLM reasoning,
testing, evaluation, and deployment remain separately inspectable.

## Week 1 capability

Week 1 builds the raw-job-text → validated-`JobPosting` foundation used by the
rest of the project:

1. deterministic HTML/whitespace cleaning,
2. a constrained Pydantic `JobPosting` schema,
3. a provider-neutral structured-LLM interface,
4. an OpenAI implementation using structured outputs,
5. a Bundesagentur Jobsuche client plus an offline 40-case fixture dataset,
6. unit tests that do not spend API credits,
7. a live evaluation script that records extraction success, missing fields,
   hallucinated fields, and mismatches.

The extractor itself does not construct an OpenAI client or load environment
variables. Those are application/setup responsibilities, so the extractor is
provider-independent and easy to test.

## Planned architecture

FastAPI → LangGraph agent → tools (job search / CV retrieval / match
scoring) → PostgreSQL + pgvector → evaluated with Ragas, traced with
Langfuse → Docker → Azure.

## Progress

| Version | Capability | Status |
|---|---|---|
| v0.1 | Job description → validated structured extraction | ✅ complete |
| v0.2 | Optional BA source + fixture fallback + extraction evaluation | ✅ complete |
| v0.3 | CV ingestion + RAG retrieval | 🔲 not started |
| v0.5 | Tool calling / agent loop | 🔲 not started |
| v0.7 | REST API + MCP server | 🔲 not started |
| v1.0 | Deployed on Azure | 🔲 not started |

## Setup

Create/activate your virtual environment, then install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and set your own API key:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Never commit `.env` or any separate text file containing a real API key.

## Run the unit tests

Run tests from the repository root:

```powershell
python -m pytest
```

The unit tests use fake clients/providers, so they should not make paid OpenAI
calls.

## Run the Week 1 live extraction evaluation

Start with 20 fixtures:

```powershell
python -m scripts.evaluate_week1 --limit 20
```

Run the complete 40-case fixture benchmark:

```powershell
python -m scripts.evaluate_week1 --limit 0
```

The report is written to:

```text
evaluation/results/week1_extraction.json
```

Week 1's minimum acceptance criterion is an extraction success rate of at least
90%. Inspect missing/hallucinated/mismatched fields as well; a high schema
success rate alone does not prove factual extraction quality.

### Week 1 validation result

The full 40-case benchmark completed successfully with `gpt-4o-mini`:

- extraction success: **40/40 (100%)**
- exact case passes: **40/40 (100%)**
- missing fields: **0**
- hallucinated fields: **0**
- mismatched fields: **0**

The fixture set contains 40 distinct job-text variants across 10 expected-output
scenarios. It is a controlled regression benchmark, not a claim of production
accuracy on the wider German job market.

## Optional: fetch live BA Jobsuche postings

```powershell
python -m scripts.fetch_ba_jobs --query "Softwareentwickler" --location "Berlin" --limit 10
```

This integration uses the public Jobsuche backend documented by the community
`bundesAPI/jobsuche-api` project. The Bundesagentur für Arbeit does not provide
this as a stable official developer API, so live requests may be rejected (for
example with HTTP 403) or change independently of this project. The live BA
source is therefore optional and is **not** a Week 1 acceptance criterion.

If the backend is unavailable, the CLI exits cleanly with an explanatory
message instead of a traceback. The stable offline source for development,
testing, and evaluation remains `data/fixtures/jobs.json`.

## Repository layout after Week 1

```text
src/
├── data_sources/
│   ├── ba_jobsuche.py
│   └── fixtures.py
├── extraction/
│   ├── cleaning.py
│   ├── extractor.py
│   └── schemas.py
└── llm/
    ├── openai_provider.py
    └── provider.py

data/fixtures/jobs.json
scripts/evaluate_week1.py
scripts/fetch_ba_jobs.py
tests/unit/
evaluation/results/
```

## Why this project

Built as a portfolio project targeting AI Engineer / Generative AI Engineer /
Agentic AI roles in Germany. Each design decision should be testable and
explainable rather than hidden behind framework magic.

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 Mehran Pashaei.
