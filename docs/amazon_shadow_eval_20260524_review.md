# Amazon Shadow Evaluation Review - 2026-05-24

## Scope

This review records a manual Amazon shadow evaluation run. It does not change product runtime, workflow retrieval, Agent prompts, reward logic, memory, grounded gates, cost gates or regression thresholds.

## Source Artifact

```text
runs/amazon_shadow_eval/20260524_120222
```

The local run artifact remains ignored by git and is not part of the release package.

## Result Summary

| Metric | Value |
| --- | --- |
| Total URLs | 20 |
| Success | 19 |
| Unavailable | 1 |
| Error | 0 |
| Average source_confidence | 0.8474 |
| Evidence preview non-empty rate | 0.95 |
| p50 latency_ms | 3303.85 |
| p95 latency_ms | 15234.83 |
| Safety failure count | 0 |
| Product API called | false |

## Metadata Completeness

| Field | Completeness |
| --- | --- |
| product_title_present | 0.95 |
| rating_present | 0.95 |
| review_count_present | 0.90 |
| category_hint_present | 0.95 |

## Unavailable URL

| Category | URL | Reason |
| --- | --- | --- |
| skincare_serum | `https://us.amazon.com/Revox-B77-Alpha-Arbutin-Brightening/dp/B09FK48BYR` | HTTP Error 404: Not Found |

## Interpretation

This run is not an adapter hard failure. The single unavailable row is a page-level 404 for one skincare serum URL, not evidence that the Amazon adapter path is structurally broken.

The Amazon shadow source quality is initially acceptable:

- 19 of 20 URLs returned `success`.
- Average source confidence is high enough for continued shadow evaluation.
- Evidence preview non-empty rate is 0.95.
- Product title, rating and category hint completeness are all 0.95.
- No safety failures were recorded.
- The runner did not call the product API.

## Safety Decision

Amazon shadow should remain debug-only.

Do not promote to `amazon_primary` yet. The current result is promising, but promotion would require repeated runs, more URL diversity, latency hardening, source-only observability and continued proof that Amazon data does not write memory or affect local regression.

## Recommended Next Step

Proceed to one of:

- L10.9-E source-only runner optimization.
- L10.9-E timeout/cache hardening.

The next iteration should focus on reducing p95 latency and isolating evaluation from full workflow cost where possible, while preserving the existing product/debug boundary.
