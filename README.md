# Job_Match_Agent

**Status: early development (Week 0/8) — not yet functional.**

An agentic AI system that matches a candidate's CV against AI/ML job postings
in Germany, explains *why* a job fits or doesn't, and ranks recommendations —
built to demonstrate real engineering judgment (deterministic logic vs. LLM
reasoning, RAG, tool calling, evaluation, and deployment), not just a
LangChain wrapper around an API call.

This repo is being built incrementally and in the open over 8 weeks. Each
tagged version (`v0.1`, `v0.2`, ...) adds one real, tested capability — see
[Progress](#progress) below.

## Planned architecture

FastAPI → LangGraph agent → tools (job search / CV retrieval / match
scoring) → PostgreSQL + pgvector → evaluated with Ragas, traced with
Langfuse → Docker → Azure.

Full design rationale (why pgvector over a dedicated vector DB, why
LangGraph, why Azure, etc.) lives in `docs/architecture.md` *(coming in
Week 5-6)*.

## Progress

| Version | Capability | Status |
|---|---|---|
| v0.1 | Job description → structured JSON extraction | 🔲 not started |
| v0.3 | CV ingestion + RAG retrieval | 🔲 not started |
| v0.5 | Tool calling / agent loop | 🔲 not started |
| v0.7 | REST API + MCP server | 🔲 not started |
| v1.0 | Deployed on Azure | 🔲 not started |

## Setup

*(To be written once there's something to set up.)*

## Why this project

Built as a portfolio project targeting AI Engineer / Generative AI Engineer /
Agentic AI roles in Germany. Every design decision is documented and
defensible in an interview — see `docs/` as it fills in.

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 Mehran Pashaei.