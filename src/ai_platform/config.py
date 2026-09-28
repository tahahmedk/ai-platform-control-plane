"""Validated, server-owned routing and admission policy."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import Provider


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ModelConfig(StrictModel):
    name: str = Field(min_length=1)
    model: str = Field(min_length=1)
    regions: set[str] = Field(min_length=1)
    capabilities: set[str] = Field(min_length=1)
    cost_per_million_tokens: float = Field(ge=0)
    p95_latency_ms: float = Field(gt=0)
    quality: float = Field(ge=0, le=1)
    reliability: float = Field(ge=0, le=1)

    def provider(self) -> Provider:
        return Provider(
            self.name,
            frozenset(self.regions),
            frozenset(self.capabilities),
            self.cost_per_million_tokens,
            self.p95_latency_ms,
            self.quality,
            self.reliability,
        )


class TenantPolicy(StrictModel):
    regions: set[str] = Field(min_length=1)
    capabilities: set[str] = Field(min_length=1)
    blocked_providers: set[str] = Field(default_factory=set)
    max_cost_per_million: float = Field(gt=0)
    token_budget: int = Field(gt=0)
    requests_per_minute: int = Field(gt=0)


class Settings(StrictModel):
    providers: list[ModelConfig] = Field(min_length=1)
    tenants: dict[str, TenantPolicy] = Field(min_length=1)
    provider_timeout_seconds: float = Field(gt=0, le=60, default=2)
    circuit_failures: int = Field(gt=0, default=2)
    circuit_cooldown_seconds: float = Field(gt=0, default=30)

    @model_validator(mode="after")
    def unique_names(self) -> "Settings":
        names = [p.name for p in self.providers]
        if len(names) != len(set(names)):
            raise ValueError("duplicate provider names")
        for policy in self.tenants.values():
            if not policy.blocked_providers.issubset(names):
                raise ValueError("unknown blocked provider")
        return self


def load_settings(path: Path | None = None) -> Settings:
    path = path or Path(__file__).with_name("defaults.json")
    return Settings.model_validate(json.loads(path.read_text(encoding="utf-8")))
