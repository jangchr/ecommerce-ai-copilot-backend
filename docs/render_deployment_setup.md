# Render Deployment Setup

Date: 2026-05-24

Scope: L11.2-B Product Mode MVP Render setup guide.

This guide documents how to deploy the current Product Mode MVP backend to Render without changing runtime behavior.

First public Render smoke results are recorded in [Render First Deployment Smoke 2026-05-24](render_first_deployment_smoke_20260524.md).

## Service Overview

| Setting | Value |
| --- | --- |
| Provider | Render |
| Service type | Web Service |
| Runtime | Docker |
| Repository | `jangchr/ecommerce-ai-copilot-backend` |
| Port binding | Render injects `PORT`; the service reads `PORT` and falls back to `8001` locally |
| Health check path | `/healthz` |
| Stable Product Mode baseline | `runs/baselines/l11_0_product_mode_mvp/` |

## Repository And Docker Settings

Current repository layout:

```text
ecommerce-ai-copilot-backend/
  Dockerfile
  main.py
  core/
  schemas/
  source_adapters/
  static/
  data/reviews/
  runs/baselines/
```

If Render is connected directly to `jangchr/ecommerce-ai-copilot-backend`, use:

```text
Root Directory: .
Dockerfile Path: Dockerfile
Docker Build Context: .
```

If this backend is later moved into a larger monorepo, use:

```text
Root Directory: backend
Dockerfile Path: backend/Dockerfile
Docker Build Context: backend
```

Do not use a Python buildpack for the first deployment. Use Docker so the same artifact boundary validated by Docker smoke is used in production.

## Runtime Environment Variables

Set these in the Render dashboard:

```dotenv
OPENAI_API_KEY=<Render secret value>
OPENAI_API_BASE=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
ALLOW_REAL_SOURCE_ADAPTERS=false
ENABLE_HF_RUNTIME_MODELS=false
MEMORY_MAX_RECORD_COUNT=500
```

Notes:

- `OPENAI_API_KEY` must be injected by Render as a secret/environment variable.
- `ALLOW_REAL_SOURCE_ADAPTERS=false` is required for the Product Mode MVP.
- `ENABLE_HF_RUNTIME_MODELS=false` is recommended for the Render public demo so Product Mode generation does not try to download or initialize Hugging Face embedding models during a request.
- `MEMORY_MAX_RECORD_COUNT=500` preserves the bounded-memory policy.
- Render injects `PORT` for Web Services. The application and Docker command read `PORT` at startup, with a local fallback of `8001`.
- Do not rely on a hard-coded `8001` binding in Render. If `PORT` is manually set, it must match the port Render expects to scan.

## Port Binding

Render detects readiness by scanning the port assigned through the `PORT` environment variable. The backend is hardened for this behavior:

```text
host = 0.0.0.0
port = int(os.getenv("PORT", "8001"))
```

Local development and Docker smoke can continue to use `8001`. Render deployments should allow the platform-injected `PORT` to drive the container bind port.

## Secret Strategy

- Never commit `.env`.
- Never copy `.env` into Docker images.
- Inject `OPENAI_API_KEY` through the Render dashboard.
- Do not print secrets in logs.
- Structured logs should remain limited to request ID, endpoint, status, latency, product category, goal and safe source-probe aggregate fields.

## Hugging Face Runtime Models

The workflow can use FAISS plus Hugging Face embeddings for semantic memory when runtime model loading is explicitly enabled. Render free or low-memory instances should not download or initialize those models during a public request.

Recommended public demo setting:

```dotenv
ENABLE_HF_RUNTIME_MODELS=false
```

With this setting, Product Mode keeps using local grounded evidence and deterministic JSON memory fallback. `generate-copilot` should not block on Hugging Face Hub availability, unauthenticated HF Hub access, model download latency, or memory pressure.

`HF_TOKEN` or `HUGGINGFACEHUB_API_TOKEN` is optional and only needed for environments that explicitly enable runtime HF models:

```dotenv
ENABLE_HF_RUNTIME_MODELS=true
HF_TOKEN=<optional Hugging Face token>
# or
HUGGINGFACEHUB_API_TOKEN=<optional Hugging Face token>
```

Do not enable this path for the public Product Mode demo until startup/runtime memory and model cache behavior are validated.

## Health Check

Configure Render health checks to:

```text
/healthz
```

Expected response:

```json
{
  "status": "ok",
  "service": "grounded-ecommerce-creative-agent",
  "stable_baseline": "l9_9_stable"
}
```

The health endpoint does not run the workflow, call an LLM, or invoke source adapters.

## Product Mode MVP Boundary

Product Mode stable inputs are the 10 local grounded slugs:

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

Production boundary rules:

- Product Mode uses local grounded reviews plus mock trend signals.
- Amazon URLs remain Debug Mode / Amazon Shadow inputs.
- Amazon URLs are not stable Product Mode inputs.
- `amazon_primary` is not enabled.
- `/api/v1/generate-copilot` must not return debug telemetry or `shadow_sources`.

## Persistent Storage Strategy

Phase 1 deployment can run without a persistent disk:

- `data/reviews/` and `runs/baselines/` are packaged release artifacts.
- Product Mode and regression anchors do not require runtime writes.
- Mutable local memory can be treated as ephemeral during first deployment.

Enable persistent disk later if production should retain:

- `storage/memory_records.json`
- FAISS index state
- embedding/cache state

If a disk is added, document:

- mount path
- backup policy
- reset/reseed path
- memory capacity monitoring
- FAISS fallback/recovery behavior

FAISS/cache persistence should be handled as a separate hardening step rather than bundled into the first Render deployment.

## Post-Deploy Smoke Checklist

Run these after Render deploy completes.

### Health

```powershell
Invoke-RestMethod -Uri "https://<render-service-host>/healthz" -Method GET
```

Expected:

- `status == "ok"`
- response includes `X-Request-ID` header

### Product Frontend

```powershell
Invoke-WebRequest -Uri "https://<render-service-host>/" -UseBasicParsing
Invoke-WebRequest -Uri "https://<render-service-host>/static/index.html" -UseBasicParsing
```

Expected:

- `/` contains `Product Mode is stable` or `balsamic_vinegar`
- `/static/index.html` contains `Copy Hook`

### Product API

```powershell
$body = @{
  url = "balsamic_vinegar"
  goal = "tiktok_ctr"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://<render-service-host>/api/v1/generate-copilot" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

Expected:

- response contains `status` and `data`
- `data` contains `insights`, `audience`, `strategy`, `assets`, `evaluation`, `feedback`
- response body does not contain `shadow_sources`
- Product output is grounded for `balsamic_vinegar`

### Debug Boundary

Only use Debug Mode or `/api/v1/debug-copilot` for internal observability. Debug endpoints may expose `shadow_sources`; Product API must not.

## Initial Recommendation

Deploy the MVP as:

```text
Render Docker Web Service
Persistent disk: off for first deployment
ALLOW_REAL_SOURCE_ADAPTERS=false
Health check: /healthz
```

Promote to persistent disk only after first deployment smoke is green and memory retention is explicitly required.
