# Amazon Shadow Evaluation Final Report

## Scope

This report closes the L10.9 Amazon shadow evaluation sequence. It is documentation-only and does not change product runtime, workflow retrieval, Agent prompts, reward logic, memory behavior, grounded gates, cost gates or regression thresholds.

Amazon remains a debug-only shadow source. It is not part of `/api/v1/generate-copilot`, does not replace the local grounded dataset, and does not write memory.

## Evaluation Timeline

| Stage | Purpose | Outcome |
| --- | --- | --- |
| L10.9-A evaluation plan | Defined the 20-URL Amazon shadow evaluation matrix, metrics and safety invariants. | Plan created in `docs/amazon_shadow_evaluation_plan.md`. |
| L10.9-B runner | Added a manual Amazon shadow evaluation runner. | Runner writes ignored artifacts under `runs/amazon_shadow_eval/<timestamp>/`. |
| L10.9-C full shadow run | Ran end-to-end debug-copilot shadow evaluation. | 19/20 success, no product API call, no safety failure. |
| L10.9-D review | Reviewed full shadow run. | Amazon source quality was promising but not ready for primary mode. |
| L10.9-E probe-only runner | Added `--probe-only` source-quality mode using `/api/v1/debug-source-probe`. | Avoids full workflow and LLM path. |
| L10.9-F probe-only run | Ran source-only evaluation. | 17/20 success, lower p95 latency, two transient errors. |
| L10.9-G comparison review | Compared full shadow and probe-only runs. | Probe-only became preferred for source quality; full shadow remains useful for end-to-end validation. |
| L10.9-H retry/error classification | Added bounded retry and normalized Amazon adapter error types. | Transient resets/timeouts retried once; deterministic failures stayed non-retry. |
| L10.9-I retry validation | Re-ran evaluation after hardening. | Confirmed improved source path stability. |
| L10.9-J/J2 classification propagation fix | Fixed `URLError` propagation so WinError details are not collapsed into generic `url_error`. | `WinError 10061` now reports `connection_refused` correctly. |

## Final Result

The final probe-only run after hardening produced:

| Metric | Value |
| --- | ---: |
| Total URLs | 20 |
| Success | 19 |
| Unavailable | 1 |
| Error | 0 |
| Safety failure count | 0 |
| Product API called | false |
| Debug Copilot called in probe-only | false |
| Probe-only mode | true |

Safety invariants held:

- `memory_write_allowed=false`
- `used_for_generation=false`
- Product API was not called.
- Debug-copilot was not called in probe-only mode.
- Amazon evidence did not enter generation.
- Amazon evidence did not write success memory.
- Local 10-category regression anchor remained unchanged.

The final hardening also verified that there is no `WinError 10061` leakage into generic `url_error`. Connection refused failures are now classified as:

```text
connection_refused
```

## Error Classification Status

The Amazon adapter now distinguishes:

| Condition | error_type | Retry? |
| --- | --- | --- |
| HTTP 404 | `not_found` | No |
| WinError 10061 or connection refused | `connection_refused` | Yes, once |
| Connection reset / WinError 10054 | `transient_connection_reset` | Yes, once |
| timeout | `timeout` | Yes, once |
| captcha or robot check | `blocked` | No |
| redirect or invalid detail page | `invalid_or_redirected_url` | No |
| parsed page has no core fields | `parse_empty` | No |
| other `URLError` | `url_error` | No |
| other exception | `unknown_error` | No |

`SourceEvidence` preserves the final `error_type` in both `data_warnings` and `metadata.error_type`, and preserves `metadata.retry_count`.

## Decision

Amazon shadow source quality has reached the threshold for continued shadow observation.

Do not promote to `amazon_primary` yet.

The adapter is good enough for debug-only source quality evaluation and UX exploration, but primary runtime would require more evidence across time, URL diversity, blocking scenarios, locale variance and memory non-pollution proof.

## Recommended Next Stage

Proceed to one of:

- L10.10 real-source shadow UX / source confidence dashboard.
- L11.0 deployment and user-facing MVP planning.

Any future promotion proposal must preserve these constraints:

- Do not directly wire Amazon into the default product runtime.
- Do not lower grounded absolute gates.
- Do not expose debug telemetry through the Product API.
- Do not remove the local dataset regression anchor.
- Do not allow real-source shadow evidence to write success memory.
