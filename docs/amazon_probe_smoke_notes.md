# Amazon Debug-Only Probe Smoke Notes

## Scope

This note records a best-effort live Amazon probe executed through:

```text
POST /api/v1/debug-source-probe
```

The probe is debug-only. It does not run `/api/v1/generate-copilot`, does not enter the product runtime, does not write memory and does not affect success/failure memory buckets.

The ten local grounded datasets remain the regression anchor:

```text
balsamic_vinegar
printer
women_bras
girls_overalls
protein_powder
phone_case
desk_lamp
baby_stroller
pet_hair_vacuum
skincare_serum
```

## Live Probe Input

| Field | Value |
| --- | --- |
| Date | `2026-05-24` |
| Endpoint | `/api/v1/debug-source-probe` |
| Provider | `amazon_review_api` |
| Product category | `balsamic_vinegar` |
| URL | `https://www.amazon.com/dp/B00QIIMCCW` |

## Live Probe Result

| Field | Value |
| --- | --- |
| Provider | `amazon_review_api` |
| Status | `success` |
| Source confidence | `0.85` |
| Evidence preview non-empty | `true` |
| Product title | `Colavita Balsamic Vinegar - 8.5 oz` |
| Rating | `4.6` |
| Review count | `485` |
| Price | Empty on parsed page |
| Category hint | `Grocery & Gourmet Food › Pantry Staples › Cooking & Baking › Cooking Oils, Vinegars & Sprays › Vinegars › Balsamic` |
| Latency | `3606 ms` |
| Fallback required | `false` |
| Memory write allowed | `false` |

### Evidence Preview

The probe returned short visible review snippets, including:

- `Brief content visible, double tap to read full content. Full content visible, double tap to read brief content. Revised 5/26/21 - Now this is listed as 8 1/2 oz for $4.99 but what came was a 17 oz bottle - still only $4.99! So it's proba...`
- `Brief content visible, double tap to read full content. Full content visible, double tap to read brief content. Fairly priced for quality Read more Read less`
- `Brief content visible, double tap to read full content. Full content visible, double tap to read brief content. Favorite balsamic besides Cento. Read more Read less`

### Parsed Bullet Points

- `Colavita Balsamic Vinegar - 8.5 oz`

## Failure Policy

Amazon pages may block, redirect, localize, rate-limit or change DOM structure. If a future live probe returns `unavailable` or `error`, do not modify the product workflow. Record the warning/error in this note or an operational run log and keep the result out of memory.

## Regression Policy

- This live Amazon probe is not a fast gate dependency.
- This live Amazon probe is not a full grounded regression dependency.
- Probe results must not write memory.
- Probe results must not enter success memory.
- Probe results must not replace `data/reviews/`.
- `/api/v1/generate-copilot` continues to use the stable local grounded dataset + mock trend path by default.

