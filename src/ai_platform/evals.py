import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EvalResult:
    groundedness: float
    answer_overlap: float
    passed: bool


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def evaluate(answer: str, reference: str, context: str, threshold: float = 0.55) -> EvalResult:
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    ans = _tokens(answer)
    ref = _tokens(reference)
    ctx = _tokens(context)
    overlap = len(ans & ref) / max(len(ref), 1)
    groundedness = len(ans & ctx) / max(len(ans), 1)
    combined = 0.55 * overlap + 0.45 * groundedness
    return EvalResult(round(groundedness, 3), round(overlap, 3), combined >= threshold)
