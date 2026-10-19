from types import SimpleNamespace

from src.extraction.schemas import JobPosting
from src.llm.openai_provider import OpenAIProvider


class FakeResponses:
    def __init__(self, parsed: JobPosting) -> None:
        self.parsed = parsed
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed: JobPosting) -> None:
        self.responses = FakeResponses(parsed)


def test_openai_provider_uses_responses_parse_with_schema() -> None:
    expected = JobPosting(role="AI Engineer")
    client = FakeClient(expected)
    provider = OpenAIProvider(client, model="test-model")  # type: ignore[arg-type]

    result = provider.generate(
        [{"role": "user", "content": "Example posting"}],
        JobPosting,
    )

    assert result == expected
    assert client.responses.kwargs["model"] == "test-model"
    assert client.responses.kwargs["text_format"] is JobPosting
