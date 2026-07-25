# Phase 2 Next Unlock Plan

## Recommended Sequence

The most stable next-stage candidates are:

1. Real DB Minimal Adapter Contract Preview
2. DB Schema Migration Dry-Run Preview
3. Audit Sink Contract Preview
4. Real LLM Sandbox Contract Preview
5. Provider Sandbox Contract Preview

Recommended order: first Real DB Minimal Adapter Contract Preview, then DB migration dry-run, then audit sink contract, then LLM sandbox, then provider sandbox.

database persistence is the smallest real integration candidate, but it is still not ready. The current work should stay in preview contracts until controls, tests, approvals, audit handling, rollback, and cost boundaries are documented and verified.

## Do Not Jump Directly To Real Production Work

The next phase should not directly perform:

- real production DB write
- real LLM production call
- real provider execution
- real platform upload
- real paid operation

## Candidate 1: Real DB Minimal Adapter Contract Preview

- Purpose: define the smallest future adapter boundary for state snapshot persistence without connecting a real database.
- Blocked controls: no real DB config, no schema migration, no real audit sink, no rollback implementation, no production approval.
- Allowed preview work: adapter interface sketch, snapshot schema contract, redaction policy, write/read failure modes, local mock replay mapping.
- Forbidden real work: no database connection, no DB write, no migration, no file export, no secret read, no external call.
- Required tests: unit tests, contract tests, mock harness replay tests, redaction tests, permission boundary tests, rollback dry-run tests.
- Approval requirements: database owner review, security review, production owner review, rollback owner review.

## Candidate 2: DB Schema Migration Dry-Run Preview

- Purpose: preview the schema migration path needed before any real persistence is considered.
- Blocked controls: no migration owner, no migration rollback plan, no data retention policy, no real audit sink.
- Allowed preview work: migration shape, dry-run fixtures, rollback checklist, sensitive-field classification, compatibility checks.
- Forbidden real work: no real migration, no backfill, no production DB write, no live customer data persistence.
- Required tests: migration contract tests, dry-run validation tests, rollback simulation tests, redaction tests, schema mismatch tests.
- Approval requirements: database owner approval, data governance approval, rollback approval, production readiness approval.

## Candidate 3: Audit Sink Contract Preview

- Purpose: define how future provider, database, LLM, and approval events would be auditable before any real sink exists.
- Blocked controls: no real audit sink, no retention policy, no trace-id owner, no production monitoring.
- Allowed preview work: event shape, trace-id contract, retention notes, redaction rules, failure handling, mock event examples.
- Forbidden real work: no database write, no real audit event, no log ingestion, no external audit service call.
- Required tests: audit preview tests, event schema tests, trace-id propagation tests, redaction tests, permission boundary tests.
- Approval requirements: audit owner review, security review, production monitoring owner review.

## Candidate 4: Real LLM Sandbox Contract Preview

- Purpose: preview the contract for a future sandbox-only LLM invocation path.
- Blocked controls: no API key approval, no secret access approval, no cost quota approval, no sandbox contract test, no production approval.
- Allowed preview work: prompt contract, output schema contract, evidence grounding requirements, timeout/cost policy, redaction policy, failure handling.
- Forbidden real work: no real LLM call, no API key read, no secret read, no external request, no paid operation, no generated production copy.
- Required tests: prompt snapshot tests, output schema tests, redaction tests, evidence grounding tests, claim-safety tests, timeout/cost tests.
- Approval requirements: provider owner approval, security approval, cost owner approval, claim-safety review, production owner review.

## Candidate 5: Provider Sandbox Contract Preview

- Purpose: preview the minimum contract for a future provider sandbox without creating a provider client.
- Blocked controls: no provider key approval, no network approval, no sandbox contract execution, no audit sink, no rollback plan, no paid-operation approval.
- Allowed preview work: provider capability contract, input/output schema, sandbox test checklist, cost/quota rules, failure taxonomy, audit packet shape.
- Forbidden real work: no provider client, no external request, no platform upload, no real file upload, no paid operation, no real retry or rollback.
- Required tests: provider contract tests, sandbox dry-run tests, schema validation tests, redaction tests, cost/quota tests, failure recovery tests.
- Approval requirements: provider owner review, security review, cost approval, network approval, audit owner review, production owner approval.
