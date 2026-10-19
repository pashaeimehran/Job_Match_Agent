from __future__ import annotations

from src.extraction.cleaning import clean_job_text
from src.extraction.schemas import JobPosting
from src.llm.provider import LLMMessage, StructuredLLMProvider


SYSTEM_INSTRUCTIONS = """Extract factual job-posting information from the user text.
Use only information explicitly supported by the posting.
Rules:
- role: the advertised job title.
- skills: explicit technical or professional skills/technologies only.
- experience_years: an exact integer only when the text states a numeric number of years; otherwise null.
- language: language names only, without proficiency wording.
- seniority: only when explicitly stated, including words such as Junior, Senior, Lead, Principal, or Staff; otherwise null.
- location: the stated work location or explicit remote location; otherwise null.
Never infer missing facts from typical industry expectations.
"""


def extract_job_posting(
    provider: StructuredLLMProvider,
    raw_text: str,
) -> JobPosting:
    """Clean raw text, extract structured facts, and return a validated JobPosting."""

    cleaned_text = clean_job_text(raw_text)
    if not cleaned_text:
        raise ValueError("Job posting text is empty after cleaning.")

    messages: list[LLMMessage] = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": cleaned_text},
    ]
    return provider.generate(messages, JobPosting)
