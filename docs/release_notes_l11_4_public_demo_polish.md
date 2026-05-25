# L11.4 Public Demo Polish Release Notes

Date: 2026-05-25

## Scope

L11.4 polishes the public Product Mode demo without changing the default product generation behavior, workflow retrieval path, Agent prompts, reward logic, routing, grounded gates, cost gates or regression thresholds.

Current public demo URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

Current stable baseline:

```text
runs/baselines/l11_0_product_mode_mvp/
```

## Included Changes

### Landing Copy Polish

- Public landing headline now explains the demo purpose:
  `Generate TikTok creative strategy from grounded ecommerce review insights.`
- The landing page states that the stable Product Mode inputs are 10 local grounded product slugs.
- `balsamic_vinegar` is recommended as the first input.
- Stable slug quick-pick buttons fill the input without automatically calling the API.
- Product Mode warns that Amazon URLs are not stable Product Mode inputs.

### Result Readability Polish

Product Mode output is now organized as a user-facing TikTok creative brief:

- Evidence Snapshot
- Target Audience & Creative Strategy
- Hook
- Storyboard
- Evaluation
- Copy Actions

Engineering-only fields such as telemetry, `shadow_sources`, `memory_observability` and raw debug trace remain hidden from Product Mode.

### Product Output Translation

New endpoint:

```text
POST /api/v1/translate-output
```

The frontend now includes:

- `Translate to Chinese`
- `Copy Chinese Translation`

The translation endpoint:

- Translates visible Product Mode Markdown/text into natural Chinese.
- Preserves Markdown structure.
- Does not run the workflow.
- Does not call source adapters.
- Does not write memory.
- Does not expose debug observability.

## Product Mode Stable Inputs

Product Mode remains stable for the 10 local grounded slugs:

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

Amazon URLs remain Debug Mode / Amazon Shadow inputs only. They are not stable Product Mode inputs, and `amazon_primary` remains disabled.

## Public Smoke Results

Smoke date: 2026-05-25

| Check | Result |
| --- | --- |
| Public `/healthz` | PASS |
| Public `/` | PASS |
| Public `/static/index.html` | PASS |
| Landing headline visible | PASS |
| Translate button visible | PASS |
| Copy Chinese Translation visible | PASS |
| `POST /api/v1/translate-output` small translation smoke | PASS |
| Translation response omits `telemetry_summary`, `shadow_sources`, `memory_observability` | PASS |
| Public `generate-copilot` live recheck | INCONCLUSIVE |

The `generate-copilot` public live recheck with `balsamic_vinegar` returned one `502 Bad Gateway` and one abrupt connection close during this audit. The Render service itself remained healthy afterward (`/healthz=ok`, `/=200`). This is recorded as a long-request/cold-start public runtime caveat rather than a local regression failure.

The earlier Render first deployment smoke remains the last documented public generation PASS and is recorded in `docs/render_first_deployment_smoke_20260524.md`.

## Known Caveat

Render cold starts or long LLM-backed generation requests may delay the first page load or first generation. Before live demos, follow `docs/public_demo_smoke_checklist.md`:

1. Warm `/healthz`.
2. Open `/`.
3. Run `balsamic_vinegar`.
4. Confirm Product Mode output before presenting.

## Boundary Confirmation

- Product API remains product-only.
- Product Mode does not expose Debug Trace, telemetry, `shadow_sources` or memory observability.
- Debug Mode still retains Debug Trace, Source Probe and Amazon Shadow Summary.
- Translation is a Product Mode user feature and does not depend on Debug Mode.
