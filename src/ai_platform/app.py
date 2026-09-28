"""Local inference sandbox; tenant labels are NOT authenticated identities."""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .budget import BudgetExceeded, RateLimited, TokenBudgetLedger
from .config import Settings, load_settings
from .guardrails import inspect_and_redact
from .models import RequestContext
from .providers import Adapter, MockAdapter, ProviderUnavailable
from .routing import NoEligibleProvider, choose_provider

logger = logging.getLogger("ai_platform")


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant: str = Field(min_length=1, max_length=80)
    region: str = Field(pattern="^(us|eu)$")
    prompt: str = Field(min_length=1, max_length=16000)
    capabilities: set[str] = Field(default_factory=lambda: {"chat"}, min_length=1)
    max_output_tokens: int = Field(default=128, gt=0, le=4096)


def create_app(
    settings: Settings | None = None, adapters: dict[str, Adapter] | None = None
) -> FastAPI:
    settings = settings or load_settings(
        Path(os.environ["AI_PLATFORM_CONFIG"]) if "AI_PLATFORM_CONFIG" in os.environ else None
    )
    app = FastAPI(title="AI Platform Control Plane", version="0.2.0")
    providers = [p.provider() for p in settings.providers]
    models = {p.name: p.model for p in settings.providers}
    adapters = adapters if adapters is not None else {p.name: MockAdapter() for p in providers}
    if set(adapters) != set(models):
        raise ValueError("adapter names must match configured providers")
    ledger = TokenBudgetLedger(
        {k: v.token_budget for k, v in settings.tenants.items()},
        {k: v.requests_per_minute for k, v in settings.tenants.items()},
    )
    app.state.ledger = ledger
    failures = {p.name: 0 for p in providers}
    open_until = {p.name: 0.0 for p in providers}
    metrics = {"requests": 0, "errors": 0, "provider_failures": 0, "fallbacks": 0}

    @app.middleware("http")
    async def trace(request: Request, call_next):
        request.state.request_id = uuid4().hex
        start = time.monotonic()
        response = await call_next(request)
        if request.url.path == "/v1/infer":
            metrics["requests"] += 1
            metrics["errors"] += int(response.status_code >= 400)
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request.state.request_id,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - start) * 1000, 2),
                }
            )
        )
        return response

    @app.get("/health/live")
    @app.get("/health/ready")
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-mock-single-process"}

    @app.get("/metrics")
    async def counters() -> dict[str, int]:
        return dict(metrics)

    @app.post("/v1/infer")
    async def infer(req: InferenceRequest, request: Request) -> dict:
        policy = settings.tenants.get(req.tenant)
        if (
            policy is None
            or req.region not in policy.regions
            or not req.capabilities <= policy.capabilities
        ):
            raise HTTPException(403, "tenant policy denied request")
        guarded = inspect_and_redact(req.prompt)
        if guarded.blocked:
            raise HTTPException(400, {"reasons": guarded.reasons})
        ctx = RequestContext(
            req.tenant,
            req.region,
            frozenset(req.capabilities),
            len(guarded.text.encode("utf-8")) + req.max_output_tokens,
            policy.max_cost_per_million,
            frozenset(policy.blocked_providers),
        )
        candidates = [p for p in providers if open_until[p.name] <= time.monotonic()]
        ranked = []
        while candidates:
            try:
                decision = choose_provider(candidates, ctx)
            except NoEligibleProvider:
                break
            ranked.append(decision)
            candidates = [p for p in candidates if p.name != decision.provider]
        if not ranked:
            raise HTTPException(503, "no eligible healthy provider")
        # Reserve all possible attempts; a timeout does not prove remote work was free.
        try:
            ledger.reserve(req.tenant, ctx.estimated_tokens * len(ranked))
        except (BudgetExceeded, RateLimited) as exc:
            raise HTTPException(429, str(exc)) from exc
        attempts = []
        for decision in ranked:
            name = decision.provider
            attempts.append(name)
            try:
                result = await asyncio.wait_for(
                    adapters[name].complete(guarded.text, req.max_output_tokens),
                    timeout=settings.provider_timeout_seconds,
                )
                if (
                    not 0 <= result.input_tokens <= len(guarded.text.encode("utf-8"))
                    or not 0 <= result.output_tokens <= req.max_output_tokens
                ):
                    raise ProviderUnavailable("adapter violated usage contract")
            except (ProviderUnavailable, TimeoutError):
                metrics["provider_failures"] += 1
                failures[name] += 1
                if failures[name] >= settings.circuit_failures:
                    open_until[name] = time.monotonic() + settings.circuit_cooldown_seconds
                continue
            except Exception:
                # Do not leak an SDK exception body, which may contain prompts or credentials.
                logger.error(
                    json.dumps(
                        {
                            "event": "adapter_contract_error",
                            "request_id": request.state.request_id,
                            "provider": name,
                        }
                    )
                )
                raise HTTPException(502, "provider adapter failed") from None
            failures[name] = 0
            output = inspect_and_redact(result.text)
            if output.blocked:
                raise HTTPException(502, "provider output blocked")
            metrics["fallbacks"] += int(len(attempts) > 1)
            logger.info(
                json.dumps(
                    {
                        "event": "inference",
                        "request_id": request.state.request_id,
                        "provider": name,
                        "attempts": len(attempts),
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                    }
                )
            )
            return {
                "request_id": request.state.request_id,
                "provider": name,
                "model": models[name],
                "text": output.text,
                "attempts": attempts,
                "score": decision.score,
                "reason": decision.reason,
                "reserved_tokens": ctx.estimated_tokens * len(ranked),
                "remaining_tokens": ledger.remaining(req.tenant),
                "usage": {
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                },
            }
        raise HTTPException(503, "all eligible providers failed")

    return app


app = create_app()
