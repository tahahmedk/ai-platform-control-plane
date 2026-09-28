"""Adapters must honor output limits and propagate cancellation."""

from dataclasses import dataclass
from typing import Protocol


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class Adapter(Protocol):
    async def complete(self, prompt: str, max_output_tokens: int) -> Completion: ...


class MockAdapter:
    async def complete(self, prompt: str, max_output_tokens: int) -> Completion:
        # UTF-8 byte accounting is conservative, not a vendor tokenizer.
        text = "Synthetic response."[:max_output_tokens]
        return Completion(text, len(prompt.encode("utf-8")), len(text))
