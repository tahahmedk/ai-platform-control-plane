from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class Provider:
    name: str
    regions: FrozenSet[str]
    capabilities: FrozenSet[str]
    cost_per_million_tokens: float
    p95_latency_ms: float
    quality: float
    reliability: float
    available: bool = True


@dataclass(frozen=True)
class RequestContext:
    tenant: str
    region: str
    capabilities: FrozenSet[str]
    estimated_tokens: int
    max_cost_per_million: float | None = None
    blocked_providers: FrozenSet[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class RoutingDecision:
    provider: str
    score: float
    reason: str
