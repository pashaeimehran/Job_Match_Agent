from __future__ import annotations

from typing import Sequence, TypeVar, cast

from openai import OpenAI
from pydantic import BaseModel

from src.llm.provider import LLMMessage, LLMProviderError


T = TypeVar("T", bound=BaseModel)


class OpenAIProvider:
    """OpenAI implementation of the provider-neutral structured LLM interface."""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    def generate(
        self,
        messages: Sequence[LLMMessage],
        schema: type[T],
    ) -> T:
        response = self._client.responses.parse(
            model=self._model,
            input=list(messages),
            text_format=schema,
        )

        parsed = response.output_parsed
        if parsed is None:
            raise LLMProviderError("OpenAI returned no parsed structured output.")

        return cast(T, parsed)
