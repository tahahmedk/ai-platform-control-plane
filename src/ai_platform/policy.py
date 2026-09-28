from .models import Provider, RequestContext


def eligible(provider: Provider, ctx: RequestContext) -> tuple[bool, str]:
    if not provider.available:
        return False, "provider unavailable"
    if provider.name in ctx.blocked_providers:
        return False, "provider blocked by tenant policy"
    if ctx.region not in provider.regions:
        return False, f"region {ctx.region!r} not supported"
    if not ctx.capabilities.issubset(provider.capabilities):
        missing = sorted(ctx.capabilities - provider.capabilities)
        return False, f"missing capabilities: {missing}"
    if (
        ctx.max_cost_per_million is not None
        and provider.cost_per_million_tokens > ctx.max_cost_per_million
    ):
        return False, "provider exceeds request cost ceiling"
    return True, "eligible"
