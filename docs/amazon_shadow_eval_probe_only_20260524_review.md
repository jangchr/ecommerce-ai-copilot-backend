# Amazon Shadow Probe-Only Evaluation Review - 2026-05-24

## Scope

This review compares the full debug-copilot Amazon shadow run with the probe-only source-quality run. It does not change product runtime, workflow retrieval, Agent prompts, reward logic, memory, grounded gates, cost gates or regression thresholds.

## Compared Runs

| Mode | Output |
| --- | --- |
| Full debug-copilot shadow | `runs/amazon_shadow_eval/20260524_120222` |
| Probe-only source evaluation | `runs/amazon_shadow_eval/20260524_125121` |

Both runs are local runtime artifacts and remain ignored by git.

## Comparison Summary

| Metric | Full debug-copilot shadow | Probe-only |
| --- | ---: | ---: |
| Total URLs | 20 | 20 |
| Success | 19 | 17 |
| Unavailable | 1 | 1 |
| Error | 0 | 2 |
| Average source_confidence | 0.8474 | 0.8471 |
| Evidence preview non-empty rate | 0.95 | 0.85 |
| p50 latency_ms | 3303.85 | 3365.41 |
| p95 latency_ms | 15234.83 | 5209.39 |
| Product API called | false | false |
| Debug-copilot called | true | false |
| Probe-only mode | false | true |

## Probe-Only Advantages

- Does not run the full workflow.
- Does not call the LLM-backed main creative path.
- Significantly reduces p95 latency compared with the full debug-copilot shadow run.
- Better suited for batch source-quality evaluation.
- Keeps product API isolated; `product API called=false`.

## Probe-Only Risks

- Success count dropped from 19 to 17.
- Two rows produced `ConnectionResetError`.
- Evidence preview non-empty rate dropped from 0.95 to 0.85.
- The lower success count suggests the direct probe path may need retry and error-classification hardening before it becomes the preferred measurement path.

## Interpretation

Probe-only mode is useful as a fast source-quality runner. It gives a cleaner read on the Amazon adapter itself because it avoids the full debug-copilot workflow and LLM path.

Full debug-copilot shadow should remain available for end-to-end shadow validation because it proves the complete debug path still carries Amazon shadow telemetry while preserving product evidence, memory and generation boundaries.

## Safety Decision

Do not promote to `amazon_primary`.

The Amazon source path is promising but not yet reliable enough for primary runtime. The observed `ConnectionResetError` rows and evidence-preview drop are acceptable for debug-only evaluation, but they are not acceptable as product evidence dependencies.

## Recommended Next Step

Proceed to retry and error-classification hardening:

- Classify `ConnectionResetError` separately from parser errors.
- Add bounded retry with jitter for transient network resets.
- Preserve no-memory-write and no-generation-use invariants.
- Keep live probe evaluation outside fast gate.
- Re-run the 20 URL evaluation after retry hardening and compare against both 2026-05-24 baselines.
