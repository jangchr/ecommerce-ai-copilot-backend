# Amazon Shadow Evaluation Plan

This document defines the offline/manual evaluation plan for Amazon real-source shadow mode. It does not change product runtime, workflow retrieval, Agent prompts, reward logic, memory, grounded gates, cost gates or regression thresholds.

## Scope

Amazon shadow evaluation is a debug-only quality study for `/api/v1/debug-copilot` and `/api/v1/debug-source-probe`.

It must not:

- Enter `/api/v1/generate-copilot` default behavior.
- Replace local dataset evidence.
- Write success memory or failure memory.
- Change the local 10-category regression baseline.
- Become a fast gate dependency.

## Candidate URL Set

Use 10-20 real Amazon product URLs across the same category spread as the local grounded baseline. The list below is the first evaluation matrix. URLs should be manually verified before each live run because Amazon pages, ASIN availability and regional redirects can change.

| id | category | url | selection intent |
| --- | --- | --- | --- |
| amz-001 | balsamic_vinegar | `https://www.amazon.com/dp/B00QIIMCCW` | Known smoke-test page for balsamic vinegar. |
| amz-002 | printer | `https://us.amazon.com/Epson-WF-C5790-Printer-Scanner-Copier/dp/B079HWMZTZ` | Printer hardware page with visible product metadata. |
| amz-003 | women_bras | `https://us.amazon.com/Triumph-Minimizer-Sensation-Seamless-Lingerie/dp/B08F1T13GV` | Apparel page where size/fit reviews may be visible. |
| amz-004 | women_bras | `https://us.amazon.com/Smart-Sexy-Cleavage-Underwire-Available/dp/B0DHGRYG59` | Second bra page to test apparel metadata variance. |
| amz-005 | protein_powder | `https://us.amazon.com/Asitis-Nutrition-Whey-Protein-Concentrate/dp/B083DXW553` | Consumable page with taste/mixability review potential. |
| amz-006 | protein_powder | `https://us.amazon.com/Max-Titanium-Concentrate-Hydrolyzed-Recovery/dp/B07ZBGBCGD` | Second supplement page for review snippet quality. |
| amz-007 | phone_case | `https://www.amazon.com/Spigen-Liquid-Designed-Moto-Stylus/dp/B0D6X6GZ8Y` | Phone case page for durability and fit signals. |
| amz-008 | phone_case | `https://www.amazon.com/OtterBox-iPhone-Symmetry-Clear-Case/dp/B0FJPWPDD2` | Second phone case page for accessory extraction stability. |
| amz-009 | desk_lamp | `https://us.amazon.com/DEWENWILS-Minimalist-Dimmable-Lighting-Standing/dp/B092V42HPT` | Lighting page with product bullets and possible packaging reviews. |
| amz-010 | desk_lamp | `https://us.amazon.com/Amazon-Basics-Adjustable-Laptop-Table/dp/B09MHB5ZXL` | Home office surface page used as a nearby desk setup control. |
| amz-011 | baby_stroller | `https://us.amazon.com/Inglesina-Aptica-Stroller-Indigo-Denim/dp/B07GRJSM4Z` | Stroller page with folding, wheel and comfort metadata. |
| amz-012 | baby_stroller | `https://us.amazon.com/Joolz-Day-Stroller-One-Hand-Comfortable/dp/B0968R16DQ` | Second stroller page for baby gear comparison. |
| amz-013 | baby_stroller | `https://us.amazon.com/Evenflo-Modular-Travel-LiteMax-Rear-Facing/dp/B0CLYS8T9Z` | Travel-system page with safety and usability metadata. |
| amz-014 | pet_hair_vacuum | `https://www.amazon.com/dp/B001EYFQ28` | Pet hair vacuum page for suction and upholstery review signals. |
| amz-015 | pet_hair_vacuum | `https://www.amazon.com/dp/B07CB6RBSP` | Cordless pet hair vacuum page for battery/noise review signals. |
| amz-016 | pet_hair_vacuum | `https://www.amazon.com/dp/B083JWGWK2` | Upright pet vacuum page for suction and hair pickup signals. |
| amz-017 | skincare_serum | `https://us.amazon.com/Lulu-Organics-Botanical-Face-Serum/dp/B07KTG4JVD` | Serum page with irritation/effectiveness review potential. |
| amz-018 | skincare_serum | `https://us.amazon.com/APLB-Skincare-elasticity-Sensitive-Revitalize/dp/B0DG8N398L` | Sensitive-skin serum page for metadata and review extraction. |
| amz-019 | skincare_serum | `https://us.amazon.com/Revox-B77-Alpha-Arbutin-Brightening/dp/B09FK48BYR` | Brightening serum page for results/irritation review signals. |
| amz-020 | skincare_serum | `https://us.amazon.com/CeraVe-Facial-Moisturizing-Lotion-Cerave/dp/B018MR63HG` | Skincare control page with structured product details. |

Only verified product-detail URLs should be used for live evaluation. Search-result URLs are not acceptable because they usually do not expose the product metadata fields required by the adapter.

## Evaluation Record Fields

Each shadow run should produce one row with these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `url` | string | Amazon product URL used for the probe. |
| `category` | string | Local baseline category mapped to the URL. |
| `provider_status` | string | `success`, `disabled`, `unavailable` or `error`. |
| `source_confidence` | float | Confidence returned by the Amazon adapter. |
| `product_title_present` | bool | Whether `metadata.product_title` is non-empty. |
| `rating_present` | bool | Whether `metadata.rating` is non-empty. |
| `review_count_present` | bool | Whether `metadata.review_count` is non-empty. |
| `evidence_preview_count` | int | Count of short evidence preview snippets. |
| `bullet_points_count` | int | Count of extracted bullet points. |
| `category_hint_present` | bool | Whether category hint metadata is non-empty. |
| `latency_ms` | float | Provider probe latency. |
| `fallback_required` | bool | Whether local grounded fallback is still required. |
| `error_type` | string | Empty on success; otherwise normalized error class. |
| `human_quality_rating` | int | Human review score from 1-5 for usefulness and correctness. |
| `notes` | string | Reviewer notes, Amazon blocking details or parsing anomalies. |

## Suggested CSV Header

```csv
url,category,provider_status,source_confidence,product_title_present,rating_present,review_count_present,evidence_preview_count,bullet_points_count,category_hint_present,latency_ms,fallback_required,error_type,human_quality_rating,notes
```

## Pass Criteria

The evaluation is informational until explicitly promoted. A candidate Amazon shadow run is considered healthy only if all hard safety rules pass and quality metrics are within reviewable bounds.

### Distribution

- Record the distribution of `success`, `unavailable` and `error`.
- A high unavailable/error rate is acceptable for shadow mode if product output is unaffected.
- Any unexpected product failure caused by shadow probing is a hard failure.

### Source Confidence

- Track mean, median and minimum `source_confidence` for successful rows.
- Proposed review target: median successful confidence at or above `0.70`.
- Confidence must not be used to approve product output in shadow mode.

### Evidence Preview Quality

- Track the non-empty evidence preview rate.
- Proposed review target: at least `70%` of successful rows have `evidence_preview_count >= 1`.
- Human reviewers should reject snippets that are page chrome, navigation text, unrelated promotions or full-page copied text.

### Metadata Completeness

Track completeness for:

- `product_title_present`
- `rating_present`
- `review_count_present`
- `bullet_points_count`
- `category_hint_present`

Proposed review target: successful rows should usually contain product title and at least one of rating, review count or bullet points.

### Latency

- Track p50 and p95 `latency_ms`.
- Proposed review target: p95 below `8000 ms` for shadow probes.
- Latency issues must not affect product generation latency because shadow mode is debug-only.

### Safety Invariants

These are hard requirements:

- `memory_write_allowed` must be `false`.
- `used_for_generation` must be `false`.
- Amazon shadow evidence must not alter `final_state.env_state.evidence`.
- Amazon shadow evidence must not enter success memory.
- Amazon shadow evaluation must not change the local 10-category regression baseline.

## Execution Policy

- This evaluation does not enter fast gate.
- This evaluation does not enter full regression gate.
- Live Amazon probes are best-effort and may fail due to blocking, localization, redirects or DOM changes.
- Any automated script for this plan must write outputs to a separate shadow report directory, not `runs/latest` product regression artifacts.

## Manual Runner

Run the manual evaluator only when the backend is already running locally:

```powershell
.\l8\Scripts\python.exe scripts\run_amazon_shadow_eval.py
```

For source quality evaluation, prefer probe-only mode:

```powershell
.\l8\Scripts\python.exe scripts\run_amazon_shadow_eval.py --probe-only
```

`--probe-only` calls:

```text
POST http://127.0.0.1:8001/api/v1/debug-source-probe
```

with:

```json
{
  "product_category": "<category>",
  "url": "<amazon_url>",
  "providers": ["amazon_review_api"],
  "debug_only": true
}
```

It does not call `/api/v1/debug-copilot`, does not run the full workflow, does not call `/api/v1/generate-copilot`, and does not write memory.

Use the full debug-copilot mode only for end-to-end shadow checks:

```powershell
.\l8\Scripts\python.exe scripts\run_amazon_shadow_eval.py
```

That mode calls:

```text
POST http://127.0.0.1:8001/api/v1/debug-copilot
```

with:

```json
{
  "url": "<amazon_url>",
  "goal": "tiktok_ctr",
  "real_source_mode": "amazon_shadow"
}
```

It does not call `/api/v1/generate-copilot`, does not write memory and does not enter fast/full regression gates. Its outputs are runtime artifacts and should not be committed.

Output location:

```text
runs/amazon_shadow_eval/<timestamp>/
  amazon_shadow_eval_summary.csv
  amazon_shadow_eval_report.md
```

## Review History

- [2026-05-24 Amazon Shadow Evaluation Review](amazon_shadow_eval_20260524_review.md)

## Promotion Review

Amazon shadow evidence can be considered for a future design review only after:

- Multiple verified URLs have been evaluated across categories.
- Success/unavailable/error distribution is understood.
- Evidence preview quality is manually rated.
- Confidence stability is measured.
- Fallback behavior is proven safe.
- Memory non-pollution is proven.
- Product/debug API boundaries remain intact.
- Local 10-category regression remains unchanged.

`amazon_primary` remains explicitly unimplemented until a separate promotion proposal is accepted.
