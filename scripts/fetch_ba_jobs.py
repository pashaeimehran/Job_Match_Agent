from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.data_sources.ba_jobsuche import BAJobsucheClient, BAJobsucheUnavailable


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch raw job texts from BA Jobsuche.")
    parser.add_argument("--query", default="AI Engineer")
    parser.add_argument("--location", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", default="data/ba_jobs.json")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100")

    client = BAJobsucheClient()
    try:
        hits = client.search_jobs(args.query, args.location, size=args.limit)
    except BAJobsucheUnavailable as exc:
        print(f"BA Jobsuche unavailable: {exc}", file=sys.stderr)
        print(
            "No live-job file was written. Week 1 can still run fully from "
            "data/fixtures/jobs.json.",
            file=sys.stderr,
        )
        return 2

    jobs = []
    for hit in hits[: args.limit]:
        reference = client.reference_number(hit)
        if not reference:
            continue
        try:
            details = client.get_job_details(reference)
        except BAJobsucheUnavailable as exc:
            print(f"Skipping {reference}: {exc}", file=sys.stderr)
            continue
        jobs.append(
            {
                "reference_number": reference,
                "raw_text": client.details_to_raw_text(details),
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(jobs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(jobs)} jobs to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
