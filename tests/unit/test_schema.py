import pytest
from pydantic import ValidationError

from src.extraction.schemas import JobPosting


def test_job_posting_accepts_valid_data() -> None:
    job = JobPosting(
        role="AI Engineer",
        skills=["Python", "LangGraph"],
        experience_years=3,
        language=["English", "German"],
        seniority="Mid-level",
        location="Berlin",
    )

    assert job.role == "AI Engineer"
    assert job.experience_years == 3


def test_job_posting_defaults_missing_optional_data() -> None:
    job = JobPosting(role="AI Engineer")

    assert job.skills == []
    assert job.language == []
    assert job.experience_years is None
    assert job.seniority is None
    assert job.location is None


@pytest.mark.parametrize("years", [-1, 51])
def test_job_posting_rejects_invalid_experience(years: int) -> None:
    with pytest.raises(ValidationError):
        JobPosting(role="AI Engineer", experience_years=years)


def test_job_posting_normalizes_lists_and_whitespace() -> None:
    job = JobPosting(
        role="  Senior   AI Engineer ",
        skills=[" Python ", "python", " LangGraph "],
        language=[" English ", "english"],
    )

    assert job.role == "Senior AI Engineer"
    assert job.skills == ["Python", "LangGraph"]
    assert job.language == ["English"]
