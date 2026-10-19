from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.data_sources.fixtures import FixtureJob, load_fixture_jobs
from src.extraction.extractor import extract_job_posting
from src.extraction.schemas import JobPosting
from src.llm.openai_provider import OpenAIProvider


SCALAR_FIELDS = ("role", "experience_years", "seniority", "location")
LIST_FIELDS = ("skills", "language")


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def compare_case(case: FixtureJob, actual: JobPosting) -> dict[str, Any]:
    expected = case.expected
    missing_fields: list[str] = []
    hallucinated_fields: list[str] = []
    mismatched_fields: list[str] = []

    for field in SCALAR_FIELDS:
        exp = getattr(expected, field)
        got = getattr(actual, field)
        if not is_missing(exp) and is_missing(got):
            missing_fields.append(field)
        elif is_missing(exp) and not is_missing(got):
            hallucinated_fields.append(field)
        elif exp != got:
            mismatched_fields.append(field)

    for field in LIST_FIELDS:
        exp_values = {value.casefold() for value in getattr(expected, field)}
        got_values = {value.casefold() for value in getattr(actual, field)}
        if exp_values - got_values:
            missing_fields.append(field)
        if got_values - exp_values:
            hallucinated_fields.append(field)

    return {
        "id": case.id,
        "passed": not (missing_fields or hallucinated_fields or mismatched_fields),
        "missing_fields": missing_fields,
        "hallucinated_fields": hallucinated_fields,
        "mismatched_fields": mismatched_fields,
        "expected": expected.model_dump(),
        "actual": actual.model_dump(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Week 1 extraction evaluation.")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of fixture cases to run. Use 0 for the full dataset.",
    )
    parser.add_argument(
        "--output",
        default="evaluation/results/week1_extraction.json",
        help="Where to write the JSON report.",
    )
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing. Add it to .env before running the live evaluation.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    provider = OpenAIProvider(OpenAI(api_key=api_key), model=model)

    cases = load_fixture_jobs()
    if args.limit > 0:
        cases = cases[: args.limit]

    results: list[dict[str, Any]] = []
    extraction_failures: list[dict[str, str]] = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case.id}")
        try:
            actual = extract_job_posting(provider, case.raw_text)
            results.append(compare_case(case, actual))
        except Exception as exc:  # live evaluation should record and continue
            extraction_failures.append(
                {
                    "id": case.id,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )

    total = len(cases)
    extracted = len(results)
    exact_passes = sum(1 for result in results if result["passed"])
    missing_count = sum(len(result["missing_fields"]) for result in results)
    hallucination_count = sum(len(result["hallucinated_fields"]) for result in results)
    mismatch_count = sum(len(result["mismatched_fields"]) for result in results)

    report = {
        "model": model,
        "cases_requested": total,
        "extractions_succeeded": extracted,
        "extraction_success_rate": extracted / total if total else 0.0,
        "exact_case_pass_rate": exact_passes / total if total else 0.0,
        "missing_field_count": missing_count,
        "hallucinated_field_count": hallucination_count,
        "mismatched_field_count": mismatch_count,
        "extraction_failures": extraction_failures,
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\nWeek 1 evaluation summary")
    print(f"Model: {model}")
    print(f"Extraction success: {extracted}/{total} ({report['extraction_success_rate']:.1%})")
    print(f"Exact case passes: {exact_passes}/{total} ({report['exact_case_pass_rate']:.1%})")
    print(f"Missing fields: {missing_count}")
    print(f"Hallucinated fields: {hallucination_count}")
    print(f"Mismatched fields: {mismatch_count}")
    print(f"Report: {output_path}")

    return 0 if report["extraction_success_rate"] >= 0.90 else 1


if __name__ == "__main__":
    raise SystemExit(main())
