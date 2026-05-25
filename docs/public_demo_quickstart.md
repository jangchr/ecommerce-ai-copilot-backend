# Public Demo Quickstart

Use this guide to try the public Product Mode demo.

Public URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

## Recommended First Input

Use:

```text
balsamic_vinegar
```

The landing page also includes a **Try balsamic_vinegar** quick-pick button. Quick-pick buttons only fill the input; they do not automatically call the API. After selecting a slug, click **Run Workflow** and wait for the result.

Render may cold start the service, so the first page load or first generation can be slower than later requests.

## Stable Product Mode Inputs

Product Mode is stable for these 10 local grounded slugs:

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

## What To Look At

The public landing copy should make the demo intent clear:

- It is a grounded ecommerce creative agent demo.
- It uses 10 stable local grounded product categories.
- It recommends starting with `balsamic_vinegar`.
- Running the workflow generates TikTok creative strategy, hook and storyboard output.
- Amazon URLs are Debug Mode / Amazon Shadow only, not Product Mode stable input.

After the workflow finishes, review:

- Evidence Snapshot: source badge, confidence indicators and short review-backed quotes.
- Target Audience: who the creative is speaking to and which trust barriers matter.
- Creative Strategy: core hook strategy, emotional trigger and CTA logic.
- Hook: the first-line TikTok creative hook.
- Storyboard: Scene 1-4 with Visual, Narration and Evidence.
- Evaluation: approved/grounded status, risk level and quality rationale.

The output is generated from local grounded review evidence plus mock trend context.

## Copy Controls

Use the copy buttons after generation:

- **Copy Hook**
- **Copy Storyboard**
- **Copy Full Markdown**
- **Translate to Chinese**
- **Copy Chinese Translation**

These are intended for quick demo handoff, review, or manual editing.

## Chinese Translation

After Product Mode generates a result, click **Translate to Chinese** to translate the visible creative brief into natural Chinese while preserving the Markdown structure. The translation uses only the Product Mode output text, not Debug Trace, telemetry, Amazon Shadow data or memory observability.

If translation fails, the original English result remains visible and unchanged.

Each major Product Mode section also has section-level translation controls at the top of the section header:

- **Translate this section**
- **Copy section translation**

Use these when you only need a Chinese version of Evidence Snapshot, Target Audience & Creative Strategy, Hook, Storyboard or Evaluation. Section translation is manual and does not run automatically, so it does not add cost unless clicked.

## Product Mode Boundaries

Product Mode stable input is the 10 local grounded slugs listed above.

Do not enter an Amazon URL in Product Mode. Amazon URLs are only for Debug Mode / Amazon Shadow checks and are not the stable product input path.

For ordinary demo use:

- Keep **Debug Mode** off.
- Do not use **Amazon Shadow**.
- Use one of the stable local slugs.

The Product API does not expose:

- `shadow_sources`
- telemetry
- memory observability

## Troubleshooting

### Page Opens Slowly

Render may cold start the service. Wait 1-3 minutes, then refresh.

### Generation Is Slow

The first generation request may load model/client dependencies and can take longer. Wait for completion before retrying.

### Page Shows 502 Or Times Out

Wait briefly and retry. If it continues, check the Render service logs.

### Amazon URL Result Is Unstable

Amazon URLs are not stable Product Mode inputs. Use Debug Mode / Amazon Shadow only when specifically testing real-source shadow behavior.

For a stable product demo, use `balsamic_vinegar` or another local grounded slug.
