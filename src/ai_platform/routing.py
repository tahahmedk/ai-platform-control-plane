from __future__ import annotations

import math
from dataclasses import dataclass

from .models import Provider, RequestContext, RoutingDecision
from .policy import eligible


@dataclass(frozen=True)
class RoutingWeights:
    quality: float = 0.40
    latency: float = 0.20
    cost: float = 0.20
    reliability: float = 0.20

    def __post_init__(self):
        values = (self.quality, self.latency, self.cost, self.reliability)
        if any(not math.isfinite(v) or v < 0 for v in values) or not math.isclose(sum(values), 1):
            raise ValueError("routing weights must be finite, nonnegative and sum to one")


class NoEligibleProvider(RuntimeError):
    pass


def _inverse_normalized(value: float, values: list[float]) -> float:
    lo, hi = min(values), max(values)
    if hi == lo:
        return 1.0
    return 1.0 - ((value - lo) / (hi - lo))


def choose_provider(
    providers: list[Provider], ctx: RequestContext, weights: RoutingWeights | None = None
) -> RoutingDecision:
    weights = weights or RoutingWeights()
    candidates: list[Provider] = []
    rejected: dict[str, str] = {}
    for p in providers:
        ok, reason = eligible(p, ctx)
        if ok:
            candidates.append(p)
        else:
            rejected[p.name] = reason
    if not candidates:
        details = "; ".join(f"{k}: {v}" for k, v in sorted(rejected.items()))
        raise NoEligibleProvider(f"no provider satisfies hard constraints ({details})")

    latencies = [p.p95_latency_ms for p in candidates]
    costs = [p.cost_per_million_tokens for p in candidates]
    ranked: list[tuple[float, Provider]] = []
    for p in candidates:
        latency_score = _inverse_normalized(p.p95_latency_ms, latencies)
        cost_score = _inverse_normalized(p.cost_per_million_tokens, costs)
        score = (
            weights.quality * p.quality
            + weights.latency * latency_score
            + weights.cost * cost_score
            + weights.reliability * p.reliability
        )
        ranked.append((score, p))

    score, winner = min(
        ranked,
        key=lambda item: (
            -item[0],
            -item[1].reliability,
            item[1].cost_per_million_tokens,
            item[1].name,
        ),
    )
    return RoutingDecision(
        provider=winner.name,
        score=round(score, 4),
        reason="hard constraints satisfied; highest policy-adjusted quality/latency/cost/reliability score",
    )
