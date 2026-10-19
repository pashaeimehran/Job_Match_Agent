from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from src.extraction.schemas import JobPosting


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "jobs.json"


class FixtureJob(BaseModel):
    id: str
    raw_text: str
    expected: JobPosting


def load_fixture_jobs(path: str | Path | None = None) -> list[FixtureJob]:
    fixture_path = Path(path) if path is not None else DEFAULT_FIXTURE_PATH
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [FixtureJob.model_validate(item) for item in payload]
