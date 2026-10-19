from typing import Sequence, TypeVar

from pydantic import BaseModel

from src.extraction.extractor import extract_job_posting
from src.extraction.schemas import JobPosting
from src.llm.provider import LLMMessage


T = TypeVar("T", bound=BaseModel)


class FakeProvider:
    def __init__(self, result: BaseModel) -> None:
        self.result = result
        self.messages: Sequence[LLMMessage] | None = None
        self.schema: type[BaseModel] | None = None

    def generate(self, messages: Sequence[LLMMessage], schema: type[T]) -> T:
        self.messages = messages
        self.schema = schema
        return self.result  # type: ignore[return-value]


def test_extractor_uses_provider_and_returns_validated_job() -> None:
    expected = JobPosting(
        role="AI Engineer",
        skills=["Python", "LangGraph"],
        experience_years=None,
        language=["English"],
        location="Munich",
    )
    provider = FakeProvider(expected)

    actual = extract_job_posting(
        provider,
        "<p>We are looking for an AI Engineer in Munich.</p><p>Python and LangGraph.</p>",
    )

    assert actual == expected
    assert provider.schema is JobPosting
    assert provider.messages is not None
    assert provider.messages[1]["role"] == "user"
    assert "<p>" not in provider.messages[1]["content"]


def test_extractor_rejects_empty_text_before_calling_provider() -> None:
    provider = FakeProvider(JobPosting(role="Unused"))

    try:
        extract_job_posting(provider, "   ")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")
