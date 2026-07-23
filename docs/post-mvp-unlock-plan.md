# Post-MVP Unlock Plan

This is a future Phase 2 plan. None of these capabilities are unlocked in the current MVP Preview Freeze. Phase 2 cannot directly enable real capabilities until the required tests, approvals, audit controls, cost guards, quota guards, and rollback plans exist and pass.

Related handoff docs:

- [Repo Handoff](repo-handoff.md)
- [Demo Guide](demo-guide.md)
- [MVP Preview Freeze](mvp-preview-freeze.md)

## Unlock Principles

- Every real capability starts disabled.
- No real capability can be enabled by frontend copy, demo state, or preview export alone.
- Each gate requires explicit tests, approvals, audit controls, and rollback or failure handling.
- Cost-bearing or quota-bearing capabilities require cost and quota guards before any paid operation.
- Policy, claim-safety, and platform-readiness checks are not legal advice and are not real platform compliance conclusions unless a future real policy integration is separately approved and validated.

## Future Capability Gates

### Real LLM Provider

- current status: disabled
- required preconditions: approved provider selection, prompt contract, evidence-bound output contract, secret management, environment gate, and operator approval boundary
- required tests: deterministic fallback tests, prompt assembly tests, evidence-reference tests, redaction tests, timeout and retry tests, and no-secret-leak tests
- required approvals: product owner approval, security approval, cost owner approval, and operator launch approval
- required audit controls: prompt preview, request metadata receipt, response metadata receipt, token usage receipt, and blocked-output log redaction
- rollback / failure handling requirement: disable provider flag, fall back to deterministic preview, surface failed call as a non-executed operator-visible error
- cost / quota requirement: token budget, per-run quota, daily quota, provider spend cap, and over-budget hard stop
- why not unlocked in MVP: MVP proves the workflow shape without transmitting prompts to a real LLM or spending tokens

### Real Image / Video / Media Provider

- current status: disabled
- required preconditions: provider contract, media requirement contract, asset manifest, upload boundary, content safety boundary, and explicit operator approval
- required tests: provider adapter tests, media manifest tests, upload/download block tests, cost estimate tests, failure recovery tests, and unsupported-format tests
- required approvals: product owner approval, media provider approval, security approval, and cost owner approval
- required audit controls: media request preview, asset reference manifest, provider response receipt, cost receipt, and blocked media action receipt
- rollback / failure handling requirement: cancel pending job where supported, mark output unavailable, keep deterministic prompt preview, and avoid storing provider artifacts
- cost / quota requirement: provider cost cap, generation count cap, resolution/duration limit, and quota exhaustion handling
- why not unlocked in MVP: MVP includes prompt and asset readiness previews, not real media generation or storage

### Real Database Persistence

- current status: disabled
- required preconditions: schema migration plan, data retention policy, tenant/project ownership model, PII classification, backup policy, and restore plan
- required tests: migration tests, write/read tests, rollback migration tests, access-control tests, retention tests, and data deletion tests
- required approvals: engineering approval, security approval, data owner approval, and operator approval for persistence activation
- required audit controls: migration receipt, write receipt, read receipt, restore receipt, deletion receipt, and access audit
- rollback / failure handling requirement: migration rollback, write disable flag, read-only fallback, and restore verification
- cost / quota requirement: storage quota, write volume cap, backup storage cap, and retention cost estimate
- why not unlocked in MVP: MVP uses request-scoped preview data and does not persist workspace state

### Real File Export

- current status: disabled
- required preconditions: export format contract, file naming policy, storage location policy, redaction policy, and operator confirmation
- required tests: JSON export tests, Markdown export tests, file write tests, path traversal tests, redaction tests, and failed-write tests
- required approvals: product owner approval, security approval, and operator export approval
- required audit controls: export preview receipt, export intent receipt, file hash receipt, storage location receipt, and redaction receipt
- rollback / failure handling requirement: delete failed partial files, keep preview-only export available, and show operator-visible failure status
- cost / quota requirement: file size cap, export count cap, storage quota, and cleanup policy
- why not unlocked in MVP: MVP supports browser preview and copy flows but does not write export files

### Real Platform Upload

- current status: disabled
- required preconditions: platform API contract, credential storage, asset and caption validation, policy check boundary, and operator launch approval
- required tests: sandbox upload tests, credential isolation tests, blocked upload tests, platform error tests, retry tests, and audit receipt tests
- required approvals: product owner approval, security approval, platform account owner approval, and operator upload approval
- required audit controls: upload preview, platform request receipt, platform response receipt, asset manifest receipt, and failure receipt
- rollback / failure handling requirement: stop retry, revoke upload attempt when supported, surface manual cleanup instructions, and disable platform connector
- cost / quota requirement: platform quota guard, API rate limit guard, and media storage quota where relevant
- why not unlocked in MVP: MVP does not publish or upload to any platform

### Real Operator Task Creation

- current status: disabled
- required preconditions: task schema, assignee model, task lifecycle, notification boundary, and duplicate prevention
- required tests: task creation tests, idempotency tests, permission tests, notification suppression tests, and cancellation tests
- required approvals: product owner approval, workspace owner approval, and operator approval
- required audit controls: task preview, creation receipt, assignee receipt, status-change receipt, and cancellation receipt
- rollback / failure handling requirement: cancel created task where supported, mark duplicate tasks, and preserve read-only preview fallback
- cost / quota requirement: task volume quota and notification rate limit
- why not unlocked in MVP: MVP shows operator task previews only and creates no real tasks

### Real Approval Token Issuance

- current status: disabled
- required preconditions: token issuer contract, token lifetime policy, revocation model, signer configuration, and approval policy
- required tests: token issuance tests, expiry tests, revocation tests, replay protection tests, signing tests, and secret isolation tests
- required approvals: security approval, product owner approval, and operator approval
- required audit controls: approval intent receipt, token issuance receipt, token revocation receipt, and signer audit
- rollback / failure handling requirement: revoke tokens, rotate signer where needed, and disable token issuance flag
- cost / quota requirement: token issuance rate limit and abuse guard
- why not unlocked in MVP: MVP previews approval state without issuing real authorization tokens

### Real External Call

- current status: disabled
- required preconditions: allowlist, timeout policy, retry policy, data minimization policy, and network egress approval
- required tests: allowlist tests, blocked-domain tests, timeout tests, retry tests, payload redaction tests, and no-secret-leak tests
- required approvals: security approval, data owner approval, and product owner approval
- required audit controls: destination receipt, payload-classification receipt, response receipt, retry receipt, and blocked-call receipt
- rollback / failure handling requirement: disable external egress, fall back to deterministic preview, and surface operator-visible network failure
- cost / quota requirement: request quota, rate limit, and provider billing cap where relevant
- why not unlocked in MVP: MVP avoids transmitting data to external services

### Real Policy Check

- current status: disabled
- required preconditions: policy API contract, claim taxonomy, evidence mapping, platform-specific rules model, and legal/compliance review
- required tests: policy adapter tests, unsupported-claim tests, missing-evidence tests, false-positive review tests, timeout tests, and fallback tests
- required approvals: product owner approval, legal/compliance review, security approval, and operator approval
- required audit controls: policy request preview, policy response receipt, decision trace, evidence reference trace, and override receipt
- rollback / failure handling requirement: mark policy status unknown, disable policy connector, and require manual review
- cost / quota requirement: API quota guard, per-run policy-check cap, and cost cap if the policy provider charges per request
- why not unlocked in MVP: MVP provides deterministic claim-safety preview only and does not produce real platform compliance conclusions

### Real Audit Logging

- current status: disabled
- required preconditions: audit schema, retention policy, log redaction policy, access model, and storage destination
- required tests: audit write tests, redaction tests, retention tests, access-control tests, query tests, and failure-mode tests
- required approvals: security approval, data owner approval, product owner approval, and operator approval
- required audit controls: audit write receipt, redaction receipt, retention receipt, access receipt, and failure receipt
- rollback / failure handling requirement: disable audit writes, preserve in-memory preview, and recover from partial write failures
- cost / quota requirement: log volume quota, retention storage cap, and query cost guard
- why not unlocked in MVP: MVP shows audit previews only and does not write database or log records

## Phase 2 Entry Gate

Phase 2 can begin only after a future change set proves:

- tests cover each real capability path and blocked fallback path
- approvals are explicit, reviewable, and revocable
- audit receipts are generated without leaking secrets or sensitive data
- cost and quota guards hard-stop paid or rate-limited operations
- rollback and failure handling are documented and tested
- disabled-by-default behavior remains intact until an operator intentionally enables a specific capability
