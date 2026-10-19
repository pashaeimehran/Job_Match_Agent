from __future__ import annotations

from typing import Literal, Protocol, Sequence, TypeVar, TypedDict

from pydantic import BaseModel


class LLMMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


T = TypeVar("T", bound=BaseModel)


class StructuredLLMProvider(Protocol):
    """Provider-neutral interface for schema-constrained LLM generation."""

    def generate(
        self,
        messages: Sequence[LLMMessage],
        schema: type[T],
    ) -> T:
        ...


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot return a parsed structured result."""
