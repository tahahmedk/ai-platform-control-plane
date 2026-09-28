# ADR-001: Keep provider SDKs out of the control plane

## Status
Accepted

## Context
Provider SDKs change quickly and expose different request/response shapes. If routing, policy, budgets, and safety depend directly on those SDKs, the platform becomes difficult to test and expensive to migrate.

## Decision
Provider-specific code belongs behind adapters. The control plane operates on provider capabilities, policy metadata, and normalized health/cost/quality signals.

## Consequences
Routing can be unit-tested without network calls. Provider migrations are isolated. The tradeoff is that provider-specific features must be deliberately surfaced through the normalized capability model rather than leaking through application code.
