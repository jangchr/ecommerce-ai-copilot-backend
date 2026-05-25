# Product Description API Contract Design

Status: L13.1-D backend endpoint draft.

## Purpose

`POST /api/v1/generate-from-description` adds a Product Description Mode for users who want a creative brief from their own product copy and pain point summary.

It is separate from the stable slug Product Mode:

- It does not change `/api/v1/generate-copilot`.
- It does not use the 10 local grounded slug retrieval path.
- It does not enable Amazon URL Product Mode.
- It does not call Amazon adapters, Source Probe or Amazon Shadow.
- It does not write memory.
- It does not add a database, login or payment.

## Request

```json
{
  "product_name": "SoftGlow Desk Lamp",
  "product_category": "desk_lamp",
  "product_description": "A compact desk lamp with soft adjustable lighting for late-night work.",
  "customer_pain_points": "Users complain about glare, messy desks, and eye fatigue at night.",
  "target_platform": "TikTok",
  "goal": "tiktok_ctr"
}
```

Required:

- `product_name`
- `product_description`
- `customer_pain_points`

Optional:

- `product_category`
- `target_platform`, default `TikTok`
- `goal`, default `tiktok_ctr`

## Validation Errors

Validation failures return HTTP 400 with safe JSON:

```json
{
  "status": "error",
  "error": "product_name is required.",
  "error_type": "missing_product_name",
  "request_id": "..."
}
```

Supported validation `error_type` values:

- `missing_product_name`
- `missing_product_description`
- `missing_customer_pain_points`
- `input_too_short`
- `input_too_long`

Generation failure returns safe JSON with `error_type="generation_failed"` and does not expose traceback, prompt text, API keys or environment secrets.

## Success Response

Success returns a Product-like creative brief:

```json
{
  "status": "success",
  "request_id": "...",
  "data": {
    "insights": {},
    "audience": {},
    "strategy": {},
    "assets": {},
    "evaluation": {},
    "feedback": ""
  }
}
```

The response follows the Product Mode visible shape:

- `data.insights`
- `data.audience`
- `data.strategy`
- `data.assets`
- `data.evaluation`
- `data.feedback`

## Source Policy

The evidence source is always:

```text
user_provided_description
```

The endpoint must not label user-provided copy as:

- Amazon review evidence
- local dataset evidence
- shadow source evidence

It also must not fabricate review evidence. `review_count` remains `0`, and `data_warnings` includes `user_provided_description_no_review_evidence`.

## Product / Debug Boundary

The endpoint must not return:

- Debug Trace
- `telemetry_summary`
- `shadow_sources`
- `memory_observability`
- raw prompt
- API key
- environment secrets
- traceback

The endpoint does not call workflow, source adapters, Amazon Shadow or memory APIs.
