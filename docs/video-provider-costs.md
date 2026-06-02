# Video Provider Cost Estimates

Status: scaffold only.

The video provider cost layer is an internal planning estimate. It does not call Runway, Pika, FAL, Veo, or any other external video API.

## Current Behavior

- `GET /api/v1/video-generation/cost/catalog` returns configurable estimate rows.
- `POST /api/v1/video-generation/cost/estimate` returns an estimate for provider, model, duration, clip count, retry count, and optional budget.
- New video jobs include `provider_payload.cost_estimate`.
- `external_api_call_planned` remains `false`.
- Manual export, generic prompt export, and CapCut shot-list export estimate as zero API cost in this app.

## Estimate Policy

- Prices are not live provider prices.
- Prices are not guaranteed.
- Free-tier assumptions are not guaranteed.
- Retries, multiple clips, higher resolution, and longer duration can multiply cost.
- Any real provider integration must do a fresh pricing review before enabling external calls.
- Any cost-incurring generation must require explicit user confirmation.

## Provider Models

The catalog includes estimate placeholders for:

- `manual_export`
- `generic`
- `capcut`
- `fal_pika_720p`
- `fal_pika_1080p`
- `fal_luma_flash`
- `fal_kling`
- `runway_gen4_turbo`
- `veo_fast`
- `veo_standard`

These are planning labels only. They are not an enabled real provider integration.

## Smoke Checklist

After deployment:

1. `GET /api/v1/video-generation/cost/catalog`
2. `POST /api/v1/video-generation/cost/estimate`
3. Generate from reviews.
4. Create a Runway or Pika video job.
5. Confirm `provider_payload.cost_estimate` is present.
6. Confirm `external_api_call_planned=false`.
7. Confirm simulated provider submit/poll still works.
8. Confirm manual result handoff still works.
