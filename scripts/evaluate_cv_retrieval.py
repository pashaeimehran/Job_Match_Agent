from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
from src.rag.embeddings import HashEmbeddings
from src.rag.service import CVService
from src.rag.store import MemoryVectorStore

ROOT = Path(__file__).resolve().parents[1]


def evaluate(service, cv_id, chunk_size, overlap, k):
    chunks = service.ingest(ROOT / "data/fixtures/sample_cv.md", cv_id, chunk_size, overlap)
    questions = json.loads((ROOT / "data/fixtures/cv_questions.json").read_text())
    rows = []
    for case in questions:
        relevant = {c.chunk_id for c in chunks if c.section == case["expected_section"]
                    and case["expected_quote"] in c.text}
        hits = service.search_cv(case["question"], cv_id, k)
        ranks = [i for i, h in enumerate(hits, 1) if h.chunk.chunk_id in relevant]
        rows.append({"id": case["id"], "expected_chunk_ids": sorted(relevant),
                     "retrieved_chunk_ids": [h.chunk.chunk_id for h in hits],
                     "hit": bool(ranks), "reciprocal_rank": 1 / ranks[0] if ranks else 0,
                     "evidence_preserved": bool(relevant)})
    return {"chunk_size": chunk_size, "overlap": overlap, "chunks": len(chunks), "k": k,
            "questions": len(rows), "hit_rate": sum(r["hit"] for r in rows) / len(rows),
            "mrr": sum(r["reciprocal_rank"] for r in rows) / len(rows),
            "evidence_coverage": sum(r["evidence_preserved"] for r in rows) / len(rows), "results": rows}


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval on a synthetic CV and 20 questions")
    parser.add_argument("--live", action="store_true", help="Use paid OpenAI embeddings and local PostgreSQL")
    parser.add_argument("--output")
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--min-hit-rate", type=float, default=0.8)
    args = parser.parse_args()
    if not 1 <= args.k <= 50 or not 0 <= args.min_hit_rate <= 1:
        parser.error("Use k in 1..50 and min-hit-rate in 0..1")
    load_dotenv()
    if args.live:
        from scripts.cv import live_service
        service, _ = live_service()
    else:
        service = CVService(HashEmbeddings(), MemoryVectorStore())
    report = {"mode": "live_semantic_postgres" if args.live else "offline_lexical_memory",
              "embedding_model": service.embeddings.model, "dimensions": service.embeddings.dimensions,
              "note": "Offline results test plumbing and lexical retrieval, not semantic quality.",
              "configurations": []}
    for size, overlap in ((64, 12), (120, 25), (300, 60), (900, 150)):
        cv_id = "evaluation-" + uuid.uuid4().hex
        try:
            result = evaluate(service, cv_id, size, overlap, args.k)
            report["configurations"].append(result)
            print(f"size={size} overlap={overlap}: hit@{args.k}={result['hit_rate']:.1%}, MRR={result['mrr']:.3f}")
        finally:
            service.store.delete(cv_id)
    output = Path(args.output or ("evaluation/results/retrieval_live.json" if args.live else "evaluation/results/retrieval_offline.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {output}")
    # Gate the default configuration; do not select the best score after observing results.
    return 0 if report["configurations"][-1]["hit_rate"] >= args.min_hit_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
