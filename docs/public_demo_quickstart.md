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

Then click **Run Workflow** and wait for the result.

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

After the workflow finishes, review:

- Evidence
- Audience
- Strategy
- Storyboard
- Evaluation

The output is generated from local grounded review evidence plus mock trend context.

## Copy Controls

Use the copy buttons after generation:

- **Copy Hook**
- **Copy Storyboard**
- **Copy Full Markdown**

These are intended for quick demo handoff, review, or manual editing.

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
