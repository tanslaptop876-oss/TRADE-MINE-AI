# TradeMind AI v1.8 Plan

## Objective

Turn the v1.7 paper-validation signals into durable, dashboard-ready operational
observability while keeping the platform in paper/shadow-only execution modes.

## Delivered foundation

- Restart-safe JSONL history for paper-validation snapshots
- Bounded history API for dashboard consumers
- Explicit validation health thresholds and computed status
- Read-only active alerts for degraded validation or persistence failure
- Aggregated observability dashboard API
- Permanent response-level confirmation that real broker dispatch is disabled

## Proposed milestones

### 1. Storage hardening

- Add retention by age and maximum record count
- Add atomic compaction and backup recovery tests
- Document migration from JSONL to a managed database if deployment scale requires it
- Add corruption and concurrent-writer test coverage

### 2. Dashboard experience

- Build validation rate, run volume, issue frequency, and health status cards
- Add filters for symbol, strategy version, and validation outcome
- Display persistence status and the real-broker-disabled safety lock
- Keep dashboard controls read-only

### 3. Alert operations

- Add acknowledgement and resolution state to an internal alert journal
- Add cooldown and deduplication rules
- Define optional outbound notification adapters behind a disabled-by-default flag
- Never let alert delivery failure affect paper execution

### 4. Reliability and security

- Add structured audit events for history and alert state changes
- Add load, recovery, and malformed-history tests
- Add authentication and authorization before exposing observability outside a trusted network
- Review data retention and sensitive-field redaction

## Safety gates and non-goals

v1.8 does not enable, invoke, or test real-money order dispatch. It does not add
broker credentials, live-order endpoints, or a path that changes
`real_broker_dispatch_enabled` from `false`.

Any future real-broker capability requires a separate proposal, threat model,
security review, explicit authorization, kill-switch validation, and a dedicated
PR with independent CI and review.
