from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobPosting(BaseModel):
    """Normalized facts extracted from a raw job advertisement."""

    model_config = ConfigDict(extra="forbid")

    # A job posting without an identifiable role is not useful downstream.
    role: str = Field(min_length=1, max_length=200)

    # The field always exists; no explicitly stated skills means an empty list.
    skills: list[str] = Field(default_factory=list)

    # None means that the posting did not state an exact numeric requirement.
    experience_years: int | None = Field(default=None, ge=0, le=50)

    # Store language names only. Proficiency wording is intentionally deferred.
    language: list[str] = Field(default_factory=list)

    # These fields are nullable because many postings do not state them explicitly.
    seniority: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=200)

    @field_validator("role")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("role must not be blank")
        return normalized

    @field_validator("skills", "language")
    @classmethod
    def normalize_string_lists(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = " ".join(value.split())
            key = normalized.casefold()
            if normalized and key not in seen:
                result.append(normalized)
                seen.add(key)
        return result

    @field_validator("seniority", "location")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None
