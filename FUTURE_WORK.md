# Future work

These are proposed engineering changes, not implemented features or a commit schedule.

## 1. Shared, durable admission

Replace the process-local ledger with transactional Postgres reservations and explicit
budget periods. Define reservation identity, retry handling and reconciliation for
uncertain provider outcomes before enabling multiple replicas.

Done when concurrent workers cannot overspend a tenant limit, duplicate requests cannot
reserve twice, and restart/failure tests demonstrate durable accounting. Authenticated
tenant resolution is a prerequisite for using this with real callers.

## 2. Measured routing evaluation

Build a reproducible synthetic workload with configurable provider latency, failure and
usage distributions. Compare the current scoring policy with simpler baselines and
report cost, tail latency and policy violations across several seeds.

Done when a routing change can be evaluated from a checked-in workload definition and
results distinguish measured behavior from the static quality values used today.

## 3. Export operational signals

Add OpenTelemetry spans and a Prometheus-compatible metrics endpoint around admission,
provider attempts and final outcomes. Keep prompts out of telemetry and avoid tenant
or request IDs as metric labels.

Done when one fallback request produces a correlated trace, bounded-cardinality
counters and a test proving that sensitive request text is absent from exported data.
