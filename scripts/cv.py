"""Run with python -m scripts.cv; all live commands are explicit."""
from __future__ import annotations

import argparse
import os
from dotenv import load_dotenv
from src.rag.service import CVService


def live_service():
    from openai import OpenAI
    from src.rag.embeddings import OpenAIEmbeddings
    from src.rag.postgres import PostgresVectorStore
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("Set DATABASE_URL in .env.")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY in .env.")
    client = OpenAI(timeout=60.0, max_retries=2)
    embeddings = OpenAIEmbeddings(client, os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                                  int(os.getenv("EMBEDDING_DIMENSIONS", "1536")))
    return CVService(embeddings, PostgresVectorStore(dsn)), client


def main():
    parser = argparse.ArgumentParser(description="CV ingestion and evidence retrieval")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("path")
    ingest.add_argument("--cv-id", required=True)
    ingest.add_argument("--chunk-size", type=int, default=900)
    ingest.add_argument("--overlap", type=int, default=150)
    for name in ("search", "ask"):
        sub = commands.add_parser(name)
        sub.add_argument("query")
        sub.add_argument("--cv-id", required=True)
        sub.add_argument("-k", type=int, default=3)
    delete = commands.add_parser("delete")
    delete.add_argument("--cv-id", required=True)
    args = parser.parse_args()
    load_dotenv()
    try:
        if args.command in {"init-db", "delete"}:
            from src.rag.postgres import PostgresVectorStore
            if not os.getenv("DATABASE_URL"):
                raise ValueError("Set DATABASE_URL in .env.")
            store = PostgresVectorStore(os.environ["DATABASE_URL"])
            if args.command == "init-db":
                store.initialize()
                print("Database schema ready.")
            else:
                store.delete(args.cv_id)
                print("CV and its stored chunks deleted (if present).")
            return 0
        service, client = live_service()
        if args.command == "ingest":
            chunks = service.ingest(args.path, args.cv_id, args.chunk_size, args.overlap)
            print(f"Stored {len(chunks)} chunks. Existing content for this CV ID was replaced.")
        elif args.command == "search":
            hits = service.search_cv(args.query, args.cv_id, args.k)
            if not hits:
                print("No stored CV evidence found for this ID.")
            for hit in hits:
                print(f"[{hit.chunk.chunk_id}] {hit.score:.4f} | {hit.chunk.section}\n{hit.chunk.text}\n")
        else:
            from src.llm.openai_provider import OpenAIProvider
            answer = service.answer(args.query, args.cv_id,
                        OpenAIProvider(client, os.getenv("OPENAI_MODEL", "gpt-4o-mini")), args.k)
            if answer.insufficient_evidence:
                print("The retrieved CV evidence does not answer this question.")
            for citation in answer.citations:
                print(f"[{citation.chunk_id}] {citation.quote}")
        return 0
    except Exception as exc:
        # Avoid printing provider payloads, CV content, credentials, or SQL parameters.
        safe = "Check database availability, input format and API configuration. Use text PDFs or Markdown for ingestion."
        print(f"CV command failed ({type(exc).__name__}): {safe}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
