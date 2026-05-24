# Amazon Real-Source Shadow Mode Plan

This document defines the design boundary for a future Amazon real-source shadow mode. It is intentionally a plan only: product runtime, workflow retrieval, Agent prompts, reward logic, routing, grounded gates, cost gates, and regression thresholds remain unchanged.

## Purpose

The current stable product path is:

```text
local grounded reviews + mock trend + LLM creative workflow
```

Amazon real-source probing already exists as a debug-only capability through `/api/v1/debug-source-probe`. The next step is to define how Amazon evidence could be compared beside the local evidence without changing product output or memory.

## Protected Boundaries

- `/api/v1/generate-copilot` remains unchanged.
- `workflow.py` default retrieval remains `local_review_dataset + tiktok_trend_mock`.
- Agent prompts, schemas, reward scoring, reflection, and routing remain unchanged.
- Grounded quality gates, cost gates, and regression thresholds remain unchanged.
- Amazon evidence does not replace local dataset evidence.
- Amazon evidence does not write to success memory or failure memory.
- The 10-category local grounded regression baseline remains the product quality anchor.

## real_source_mode

| Mode | Status | Behavior |
| --- | --- | --- |
| `local` | Default | Product runtime uses local review datasets and mock trend signals. Full regression and release gates use this mode. |
| `amazon_shadow` | Design-only next step | Amazon evidence is fetched as a side-channel for debug observability only. It is compared against local evidence but does not affect product evidence, strategy, reward, memory, or regression gates. |
| `amazon_primary` | Not implemented | Would allow Amazon evidence to influence product runtime only after a separate promotion review. This mode is explicitly out of scope for L10.8. |

`amazon_shadow` must require an explicit debug/admin activation path. It must not be enabled merely because `ALLOW_REAL_SOURCE_ADAPTERS=true`.

## Amazon Shadow Data Flow

1. Product workflow runs normally with local evidence.
2. Amazon source probe runs as a side-channel only when explicitly requested in debug context.
3. Probe output is attached to debug observability, not to product evidence.
4. `env_state.evidence`, `raw_reviews`, strategy input, reward metrics, and memory records continue to use the local grounded path.
5. Any Amazon probe failure is recorded as shadow telemetry and does not trigger product fallback, reflection, or memory writes.

## Shadow Output Fields

The debug observability payload should expose these fields:

| Field | Meaning |
| --- | --- |
| `amazon_source_status` | `success`, `disabled`, `unavailable`, or `error`. |
| `amazon_source_confidence` | Confidence returned by the Amazon adapter. |
| `amazon_product_title` | Parsed Amazon product title when available. |
| `amazon_review_count` | Parsed review count when available. |
| `amazon_evidence_preview_count` | Count of short evidence preview snippets. |
| `amazon_latency_ms` | Probe latency for the Amazon adapter call. |
| `amazon_error` | Error or unavailability reason, empty when successful. |

Example shape:

```json
{
  "real_source_shadow": {
    "mode": "amazon_shadow",
    "amazon_source_status": "success",
    "amazon_source_confidence": 0.82,
    "amazon_product_title": "Example product",
    "amazon_review_count": "485",
    "amazon_evidence_preview_count": 3,
    "amazon_latency_ms": 1200.5,
    "amazon_error": ""
  }
}
```

## Failure Behavior

- If Amazon blocks, times out, or returns unusable markup, record `amazon_source_status="unavailable"` or `"error"` and preserve `amazon_error`.
- If the request is missing a valid Amazon URL, record an unavailable status.
- If evidence preview quality is low, keep the result in shadow only and mark confidence accordingly.
- Product output, local evidence, memory, and regression artifacts remain unaffected.

## Memory Policy

- `memory_write_allowed=false` for Amazon shadow data.
- Amazon shadow evidence is excluded from success/failure memory records.
- Amazon shadow fields are excluded from memory fingerprints.
- Any proof that Amazon shadow data entered success memory is a hard blocker.

## Regression Policy

- Fast and full regression continue to validate the local 10-category grounded baseline.
- Live Amazon behavior is best-effort and must not be a hard dependency for CI.
- Mocked tests may validate shadow contract and failure behavior.
- Shadow reports can be archived separately from `runs/latest` product regression artifacts.

## Promotion Conditions

Amazon evidence can be considered for a future `amazon_primary` design only after all conditions below are satisfied:

- Multi-URL success rate is measured across varied Amazon product pages and reviewed as stable.
- Evidence previews are short, review-like, non-boilerplate, and not page chrome.
- Source confidence is stable across repeated runs and does not oscillate around approval thresholds.
- Fallback behavior is proven: Amazon unavailable/error states never break product output.
- Memory non-pollution is proven by tests and regression artifacts.
- Local dataset regression remains unchanged and continues to pass.
- Product/debug API boundaries remain intact.

## Promotion Review Checklist

Before any implementation beyond shadow mode:

- Add fixture-based adapter tests for successful, blocked, malformed, and sparse Amazon pages.
- Add debug telemetry tests for all required shadow fields.
- Prove no writes to success memory from Amazon shadow data.
- Run full local regression and confirm 10/10 categories still pass.
- Document accepted risks, failure modes, and rollback behavior.

## L10.8-A Exit Criteria

- This design document exists and is linked or discoverable from project docs.
- No runtime behavior changes are made.
- Fast regression passes after adding the document.
