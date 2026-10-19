# CareerMatch AI / Job_Match_Agent

A Germany-focused job matching portfolio project. Implemented capabilities are
structured job extraction and CV ingestion with evidence retrieval. Job-CV
ranking, agent orchestration, and the web API remain planned.

## Implemented capabilities

- Job text cleaning, Pydantic validation, provider-independent structured outputs.
- Optional BA Jobsuche client and a controlled 40-case extraction fixture set.
- PDF, Markdown and text CV ingestion with deterministic section-aware chunks.
- Batched OpenAI embeddings, PostgreSQL/pgvector storage, exact cosine retrieval.
- CV-scoped search, atomic replacement, embedding configuration checks and deletion.
- Extractive CV Q&A with checked source IDs and verbatim quotations.
- Synthetic CV, 20 retrieval questions, chunk-size comparison and offline tests.

PostgreSQL integration and live OpenAI retrieval have been validated locally.
The default configuration achieved 20/20 hit@3 on the synthetic benchmark.
Both offline lexical and live semantic retrieval reports are included.

## Setup and commands

Use Python 3.11 or newer and a virtual environment. From the project root:

```powershell
python -m pip install -r requirements-retrieval.txt
python -m pytest
python -m scripts.evaluate_cv_retrieval
```

Preserve your existing `.env`; add the new database and embedding settings from
`.env.example`. Install and start Docker Desktop before database commands.

```powershell
docker compose up -d --wait
python -m scripts.cv init-db
python -m scripts.cv ingest data/fixtures/sample_cv.md --cv-id demo
python -m scripts.cv search "What is the German language level?" --cv-id demo
python -m scripts.cv ask "What is the German language level?" --cv-id demo
```

Ingest, search and ask use paid OpenAI calls. CV chunks are sent to OpenAI for
embeddings; ask sends retrieved chunks for answer selection. Start with the
synthetic fixture. Keep personal documents in ignored `data/private/`.
See [the application guide](docs/apply_cv_retrieval.md) for all setup, evaluation,
troubleshooting and Git commands.

## Validation status

Local Windows validation passed all 36 offline tests and the separate
PostgreSQL integration test. Dependency installation completed successfully.
Live Q&A returned a source-backed German B1 answer and abstained when asked
about salary, which the synthetic CV does not specify. These two checks are
smoke tests, not a comprehensive answer-quality evaluation.

The supplied job extraction report records 40/40 exact fixture passes. It was
renamed without changing its measurements; no paid extraction run was repeated.
The set covers 40 variants across 10 output scenarios, not real-world accuracy.

```powershell
python -m scripts.evaluate_job_extraction --limit 0
```

That command makes paid calls and writes
`evaluation/results/job_extraction_evaluation.json`.

See [retrieval results](benchmarks/retrieval_baseline.md) and
[architecture](docs/cv_retrieval_architecture.md).

## Optional BA Jobsuche source

```powershell
python -m scripts.fetch_ba_jobs --query "Softwareentwickler" --location "Berlin" --limit 10
```

This uses an unofficial public backend described by the community
`bundesAPI/jobsuche-api` project, not a guaranteed developer API. HTTP 403 and
other failures are handled gracefully. Use `data/fixtures/jobs.json` for
repeatable development when the live source is unavailable.

## Repository layout

```text
src/data_sources/       Optional live job source and fixtures
src/extraction/         Structured job extraction
src/llm/                Structured generation provider interface
src/rag/                CV parsing, embeddings, stores, retrieval, Q&A
scripts/                Extraction evaluation, CV CLI, retrieval evaluation
tests/unit/             Offline regression tests
tests/integration/      Opt-in PostgreSQL checks
data/fixtures/          Synthetic public examples and evaluation labels
docs/                   Setup and architecture
benchmarks/             Measured results and limitations
```

## License

[MIT](LICENSE). Copyright © 2026 Mehran Pashaei.
