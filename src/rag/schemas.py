from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CVDocument(StrictModel):
    cv_id: str = Field(min_length=1, max_length=120)
    source_name: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    text: str = Field(min_length=1)


class CVChunk(StrictModel):
    chunk_id: str
    cv_id: str
    section: str
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class SearchHit(StrictModel):
    chunk: CVChunk
    score: float = Field(ge=-1, le=1)


class Citation(StrictModel):
    chunk_id: str
    quote: str = Field(min_length=1)


class EvidenceAnswer(StrictModel):
    # Extractive by design: each answer statement must be a source substring.
    citations: list[Citation]
    insufficient_evidence: bool
