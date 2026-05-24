# Render First Deployment Smoke

Date: 2026-05-24

Render service URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com
```

## Smoke Results

| Check | Result |
| --- | --- |
| Public `/healthz` | PASS |
| Public `/` | PASS |
| Public `/static/index.html` | PASS |
| Public Product Mode UI | PASS |
| Public `/api/v1/generate-copilot` | PASS |

## Product Mode Test

Input:

```text
balsamic_vinegar
```

Observed result:

| Field | Value |
| --- | --- |
| Source | `local_dataset+mock` |
| Review confidence | `0.75` |
| Evidence alignment | `1.00` |
| Grounded | `true` |
| Approved | `true` |

Copy controls:

- `Copy Hook`: usable
- `Copy Storyboard`: usable
- `Copy Full Markdown`: usable

## Production Boundary Confirmation

- Product Mode still uses the 10 stable local grounded slugs.
- Amazon URLs remain Debug Mode / Amazon Shadow inputs.
- Amazon URLs are not stable Product Mode inputs.
- `ALLOW_REAL_SOURCE_ADAPTERS=false`.
- Product API does not expose:
  - `shadow_sources`
  - `telemetry_summary`
  - `memory_observability`

## Notes

This first deployment smoke confirms that Render can serve:

- the FastAPI health endpoint,
- the static Product Mode UI,
- static assets through `/static/index.html`,
- and the default Product Mode generation path for `balsamic_vinegar`.

Persistent disk was not required for this first smoke. If production memory retention becomes required, enable persistent storage separately and document the mount path, backup policy and reset path.
