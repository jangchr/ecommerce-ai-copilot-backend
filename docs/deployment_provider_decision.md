# Deployment Provider Decision

Date: 2026-05-24

Scope: L11.2-A Product Mode MVP deployment provider decision.

This document compares low-friction deployment targets for the grounded ecommerce creative agent backend. It does not change runtime behavior, workflow logic, Agent prompts/schemas/reward/routing, API contracts, regression gates or cost gates.

## Current Application Needs

The current Product Mode MVP needs:

- Docker deployment from the existing `Dockerfile`.
- Python 3.12-compatible runtime.
- Runtime environment variables for `OPENAI_API_KEY`, `OPENAI_API_BASE`, `MODEL_NAME`, `ALLOW_REAL_SOURCE_ADAPTERS=false` and `MEMORY_MAX_RECORD_COUNT=500`.
- `/healthz` health check support.
- Static frontend serving from `/` and `/static/index.html`.
- Logs for request IDs and structured JSON events.
- Optional persistent storage for `storage/memory_records.json` and FAISS/cache state if production memory persistence is enabled.
- A low-cost path that can run a small FastAPI + LLM-orchestrating backend without changing the Product Mode MVP runtime.

The current stable product path remains:

```text
local grounded reviews + mock trend + LLM creative workflow
```

Amazon real-source behavior remains Debug Mode / Amazon Shadow only.

## Provider Comparison

| Provider | Docker Support | Python 3.12 | Env Vars / Secrets | Persistent Storage | Cold Start | Low-Cost Fit | Health Check | Logs | Product Mode MVP Fit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Render | Strong. Web services can deploy from repo or prebuilt Docker image. | Yes via Docker image. | Built-in environment variables/secrets. | Persistent disks available on paid services. | Free/idle instances may cold start; paid web services better. | Good for first public MVP; paid plan recommended for reliability. | Built-in health check path. | Good built-in service logs. | Best first choice. |
| Railway | Strong. Builds with Dockerfile if present. | Yes via Docker image. | Built-in variables; injects `PORT`. | Volumes available; deployments with volumes may have downtime behavior. | Generally low friction; runtime depends on plan/activity. | Good for fast iteration and demos. | Healthcheck endpoint supported for deploy readiness. | Good developer logs. | Good alternate choice, especially for developer velocity. |
| Fly.io | Strong. Dockerfile-first deployment path. | Yes via Docker image. | Secrets and env configuration through Fly tooling. | Volumes available but tied to Machines/regions and need replication design. | Good if Machines stay warm; more infra concepts. | Good for global edge/region control, less beginner-simple. | Health checks supported through Fly config/proxy expectations. | Strong machine logs/observability. | Good technical fit, but more operational overhead than needed for MVP. |
| DigitalOcean App Platform | Supports app deployment from Git/container images and health checks. | Yes via Docker image. | App/service environment variables. | App Platform storage story is less direct for this app; external storage or different DO primitives may be needed for durable memory. | Managed PaaS behavior; less transparent than VM/container control. | Predictable and familiar, but not the simplest for persistent file-backed memory. | Built-in health checks. | Platform logs available. | Acceptable, but persistent memory needs more design. |
| AWS Lightsail Containers | Supports container services, env vars and public endpoint health checks. | Yes via Docker image. | Container deployment env vars. | Container service filesystem should be treated as ephemeral; durable memory needs external storage or different AWS service. | Usually predictable container service, but AWS setup overhead remains. | Cost can be predictable, but operational surface is AWS-flavored. | Public endpoint health checks configurable. | Container logs/metrics available. | Acceptable if AWS is preferred, not ideal as first MVP path. |

## Recommendation

Recommended first deployment path:

```text
Render Web Service using Dockerfile
```

Why Render first:

- It matches the current artifact shape: one Dockerized FastAPI backend that serves both API and static Product Mode UI.
- It supports Docker deployment, environment variables/secrets, health checks and service logs with minimal project restructuring.
- It supports persistent disks on paid services, which is useful if/when `storage/memory_records.json` or FAISS/cache state should persist.
- It is simple enough for Product Mode MVP handoff while still allowing a clean upgrade path.

Recommended Render configuration:

- Runtime: Docker web service from this repo.
- Start command: default image command, `uvicorn main:app --host 0.0.0.0 --port 8001`, unless the platform requires binding to its injected port.
- Health check path: `/healthz`.
- Environment:
  - `OPENAI_API_KEY`
  - `OPENAI_API_BASE=https://api.deepseek.com/v1`
  - `MODEL_NAME=deepseek-chat`
  - `ALLOW_REAL_SOURCE_ADAPTERS=false`
  - `MEMORY_MAX_RECORD_COUNT=500`
- Validate after deploy:
  - `GET /healthz`
  - `GET /`
  - `GET /static/index.html`
  - Product Mode slug smoke with `balsamic_vinegar`

## Alternate Path

Use Railway if deployment speed and developer experience matter more than long-lived persistent memory:

- Dockerfile deployment is straightforward.
- Health checks are easy to configure.
- Good for short demos and rapid iteration.
- If persistent memory becomes important, volume behavior should be explicitly tested before treating it as production-durable.

Use Fly.io if regional control, edge deployment or low-level machine control becomes important:

- Strong Docker fit and secrets support.
- Volumes require more explicit operational design.
- Better as a second-stage infrastructure choice than a first MVP deployment.

Use DigitalOcean App Platform or AWS Lightsail Containers if the broader cloud account/vendor strategy already points there:

- Both can run containerized apps with environment variables and health checks.
- Both require more care around durable file-backed memory for this project.

## Decision

For the next deployment step:

```text
Primary: Render
Fallback/alternate: Railway
Defer: Fly.io, DigitalOcean App Platform, AWS Lightsail Containers
```

Do not enable real Amazon/TikTok/Reddit source adapters as part of first deployment. Keep:

```dotenv
ALLOW_REAL_SOURCE_ADAPTERS=false
```

Keep `data/reviews/` and `runs/baselines/l11_0_product_mode_mvp/` packaged as release artifacts.

## Sources

- Render web services: https://render.com/docs/web-services/
- Render Docker: https://render.com/docs/docker
- Render health checks: https://render.com/docs/health-checks
- Render environment variables: https://render.com/docs/environment-variables
- Railway deployments: https://docs.railway.com/deployments/reference
- Railway healthchecks: https://docs.railway.com/reference/healthchecks
- Railway free trial/pricing: https://docs.railway.com/pricing/free-trial
- Fly.io Dockerfile deploy: https://fly.io/docs/languages-and-frameworks/dockerfile/
- Fly.io secrets: https://fly.io/docs/apps/secrets/
- Fly.io volumes: https://fly.io/docs/volumes/overview/
- DigitalOcean App Platform health checks: https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/
- DigitalOcean App Platform app spec: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
- DigitalOcean App Platform pricing: https://docs.digitalocean.com/products/app-platform/details/pricing/
- AWS Lightsail containers: https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-container-services.html
- AWS Lightsail billing: https://docs.aws.amazon.com/en_us/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html
