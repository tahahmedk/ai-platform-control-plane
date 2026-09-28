# ADR-002: Conservative admission and bounded fallback
Status: accepted for the local sandbox.

A client estimate cannot enforce capacity. The service counts input UTF-8 bytes,
adds the output limit, and reserves that amount for every eligible attempt under
one lock. Failed and unused reservations remain charged: remote cancellation cannot
prove that no billable work occurred. This is capacity admission, not accurate
billing. The lifetime budget has no automatic reset.

Fallback reuses hard regional/capability/cost policy. Adapters normalize transient
errors; unexpected programming errors remain errors rather than silently retrying.
Timeouts depend on cooperative async adapters. A blocking SDK must be isolated.

Counters and circuit state are process local. The sandbox therefore uses one
replica and one worker; HPA is an explicitly separate future design. A production
version needs shared durable admission, authenticated identities and adapter usage
reconciliation before horizontal scaling.

Routing scores are relative to eligible candidates, so removing a failed model
can alter the normalized ordering of remaining models. Ties must be deterministic.
