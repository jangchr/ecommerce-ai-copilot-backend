# Production Handoff Runbook

## Purpose

This runbook hands off operation of the grounded ecommerce creative agent backend from development to release, staging and production ownership. It consolidates startup, validation, observability, storage and incident-response procedures without changing runtime behavior.

Current stable baseline:

```text
runs/baselines/l9_9_stable/
```

Latest accepted production handoff baseline:

```text
runs/baselines/l10_4_production_handoff/
```

Current Product Mode MVP baseline:

```text
runs/baselines/l11_0_product_mode_mvp/
```

## Safety Posture

| Boundary | Operating Rule |
| --- | --- |
| Default source policy | Keep `ALLOW_REAL_SOURCE_ADAPTERS=false`; local review datasets and mock trend signals remain the regression anchors. |
| Product output | `/api/v1/generate-copilot` returns product content only; it must not expose `request_id`, `telemetry_summary`, memory state or other debug internals in the response body. |
| Debug output | `/api/v1/debug-copilot` and `/api/v1/debug-source-probe` are diagnostic surfaces and should be access-controlled outside local development. |
| Health polling | `/healthz` is safe for liveness/readiness polling because it does not invoke workflow, LLM calls or source adapters. |
| Correlation and logs | Every response returns `X-Request-ID`; structured logs use the request ID and safe summary fields only. |
| Memory | Only grounded, approved outcomes qualify for success memory; memory capacity remains bounded. |

## Amazon Shadow Source Status

Amazon real-source work is currently debug-only and shadow-only:

- `amazon_review_api` can be evaluated through `/api/v1/debug-source-probe`.
- `/api/v1/debug-copilot` can return `shadow_sources` only when `real_source_mode=amazon_shadow`.
- `/api/v1/generate-copilot` does not call Amazon and does not return `shadow_sources`.
- Shadow evidence is not used for generation.
- Shadow evidence does not write memory.
- `memory_write_allowed=false` and `used_for_generation=false` are hard observability invariants.
- `amazon_primary` remains unimplemented and must not be enabled without a separate promotion review.

The current status is documented in [L10.10 Amazon Shadow Observability Release Notes](release_notes_l10_10_amazon_shadow_observability.md).

## Product Mode MVP Status

L11.0 Product Mode is the current local demo surface:

- `GET /` serves the static frontend.
- The default Product Mode input is `balsamic_vinegar`.
- Product Mode should use the 10 stable local grounded slugs:
  - `balsamic_vinegar`
  - `printer`
  - `women_bras`
  - `girls_overalls`
  - `protein_powder`
  - `phone_case`
  - `desk_lamp`
  - `baby_stroller`
  - `pet_hair_vacuum`
  - `skincare_serum`
- Amazon URLs remain Debug Mode / Amazon Shadow inputs and are not stable Product Mode inputs.
- Debug Mode Off hides Debug Trace, Source Probe, Amazon Shadow and debug-only observability.
- Copy controls are available for Product Mode output: `Copy Hook`, `Copy Storyboard` and `Copy Full Markdown`.

The current Product Mode MVP status is documented in [L11.0 Product Mode MVP Release Notes](release_notes_l11_0_product_mode_mvp.md).

## L11.4 Public Demo Polish Status

L11.4 improves the public demo presentation layer while preserving Product Mode runtime behavior:

- Landing copy now explains the grounded ecommerce creative agent demo.
- The 10 stable local grounded slugs are visible as quick-pick inputs.
- Product results are organized as a user-facing TikTok creative brief.
- Product Mode includes `Translate to Chinese` and `Copy Chinese Translation`.
- Product Mode includes section-level `Translate this section` and `Copy section translation` controls for visible Product output.
- Translation uses `/api/v1/translate-output`, does not run workflow, does not write memory and does not expose debug observability.
- The frontend uses relative API paths for public deployment.
- Render port binding reads the injected `PORT` value and falls back to `8001` locally.
- Render public demo uses `ENABLE_HF_RUNTIME_MODELS=false` to avoid request-time Hugging Face embedding model loading.
- Public `generate-copilot` recovered from prior `502` / abrupt-close behavior and returned `200 OK` for `balsamic_vinegar`.
- Amazon URLs remain Debug Mode / Amazon Shadow inputs only.

Current status is documented in [L11.4 Public Demo Polish Release Notes](release_notes_l11_4_public_demo_polish.md).
Final L11.4 public demo status is documented in [L11.4 Public Demo Final Release Notes](release_notes_l11_4_public_demo_final.md) and [Public Demo Polish Final Audit](public_demo_polish_final_audit.md).

## L12.0 Commercial MVP Planning Status

L12.0 moves the project from technical public demo completion toward commercial MVP definition:

- Target users are mapped across sellers, marketers, creators, brand owners and agencies.
- The recommended beachhead is the small ecommerce brand owner, with TikTok ad creative freelancers / small agencies as a strong secondary segment.
- The current value proposition is: generate grounded TikTok ad hooks and storyboards from ecommerce review pain points, with one-click Chinese translation.
- The next MVP remains scoped around Product Mode polish, copy controls, translation and stable Render deployment.
- The next MVP explicitly excludes login, payment, database history, Amazon URL as default Product input, team collaboration and `amazon_primary`.

Commercial planning is documented in [Commercial MVP Scope](commercial_mvp_scope.md).

## L12.1-A Product Output Download Actions

Status: ready.

Product Mode now includes client-side export actions:

- **Download Markdown** exports the visible Product brief as `creative_brief_<slug>_<timestamp>.md`.
- **Download JSON** exports the visible Product brief as `creative_brief_<slug>_<timestamp>.json`.
- Downloads include Product Mode visible content and any generated full or section-level Chinese translations.
- Downloads do not include Debug Trace, telemetry, `telemetry_summary`, `shadow_sources`, `memory_observability`, Source Probe output, Amazon Shadow Summary, API keys or environment secrets.
- No backend endpoint, database, login or payment was added.

## L12.1-B Local Recent Generations

Status: ready.

Product Mode now includes browser-local recent generation history:

- Recent records are stored in localStorage under `crossgrowth_recent_generations_v1`.
- The browser keeps at most 10 Product Mode results, newest first.
- Each record shows input slug, generated timestamp, hook summary, **View**, **Copy Markdown** and **Delete**.
- **View** restores a saved Product Mode result without calling `/api/v1/generate-copilot`.
- **Copy Markdown** copies saved Product Mode Markdown only.
- **Clear Recent Generations** clears the local browser history.
- Saved records include Product Mode user-visible fields and any generated full or section-level Chinese translations.
- Saved records do not include Debug Trace, telemetry, `telemetry_summary`, `shadow_sources`, `memory_observability`, Source Probe output, Amazon Shadow Summary, API keys or environment secrets.
- No backend endpoint, database, login or payment was added.

## L12.2-A Static Example Gallery

Status: ready.

Product Mode now includes a static Example Gallery:

- The first gallery cards cover `balsamic_vinegar`, `pet_hair_vacuum` and `desk_lamp`.
- Each card shows a pain point summary, hook summary and storyboard summary.
- **Try This Product** fills the Product Mode input with the card slug only.
- Gallery clicks do not call `/api/v1/generate-copilot`, do not open Debug Mode, do not run Source Probe, do not run Amazon Shadow and do not save to Recent Generations.
- The gallery does not display or read Debug Trace, telemetry, `telemetry_summary`, `shadow_sources` or `memory_observability`.
- No backend endpoint, database, login or payment was added.

## L13.1-D Product Description Backend Endpoint

Status: draft implementation.

`POST /api/v1/generate-from-description` adds a Product Description Mode backend surface:

- It accepts `product_name`, `product_description`, `customer_pain_points`, optional `product_category`, optional `target_platform`, and optional `goal`.
- It returns the Product-like visible shape: `insights`, `audience`, `strategy`, `assets`, `evaluation`, and `feedback`.
- The evidence source is always `user_provided_description`.
- It does not change `/api/v1/generate-copilot`.
- It does not call source adapters, Amazon adapter, Source Probe, Amazon Shadow, workflow memory, database, login, or payment.
- It does not return Debug Trace, `telemetry_summary`, `shadow_sources`, `memory_observability`, raw prompt, traceback, API keys, or environment secrets.

Contract details are documented in [Product Description API Contract Design](product_description_api_contract_design.md).

## L13.1-E Product Description Frontend Implementation

Status: draft implementation.

The public demo page now includes **Product Description Mode** between stable slug quick-picks and Example Gallery:

- Required fields: Product name, Product description and Customer pain points.
- Optional fields: Product category, Target platform and Goal.
- **Generate from description** calls `/api/v1/generate-from-description`.
- Successful results reuse the Product Result renderer and enable Copy, Download, Translation and Recent Generations.
- The result source is `user_provided_description`.
- This mode does not call stable slug `/api/v1/generate-copilot`, Debug Copilot, Source Probe, Amazon Shadow or Amazon adapters.
- It does not display or save Debug Trace, telemetry, `telemetry_summary`, `shadow_sources` or `memory_observability`.
- No backend endpoint beyond L13.1-D, database, login or payment was added.

The recommended first external deployment target is documented in [Deployment Provider Decision](deployment_provider_decision.md). Current recommendation: Render first, Railway as the closest alternate, with `ALLOW_REAL_SOURCE_ADAPTERS=false` preserved for the Product Mode MVP.

Render-specific setup is documented in [Render Deployment Setup](render_deployment_setup.md), including Docker settings, required environment variables, `/healthz`, Product Mode frontend smoke, and the first-deployment persistent-storage decision.

The first public Render deployment smoke passed for `https://ecommerce-ai-copilot-backend.onrender.com` and is recorded in [Render First Deployment Smoke 2026-05-24](render_first_deployment_smoke_20260524.md).

The public Product Mode handoff audit is recorded in [Public Product Mode Handoff Audit](public_product_mode_handoff_audit.md).

External demo users should start with [Public Demo Quickstart](public_demo_quickstart.md).

Before live demos, use [Public Demo Smoke Checklist](public_demo_smoke_checklist.md) to warm the Render service and confirm Product Mode readiness.

## Startup Sequence

Perform startup in this order:

1. Confirm the deployment artifact includes application source, `data/reviews/`, and `runs/baselines/l9_9_stable/`.
2. Inject environment configuration at runtime. Never bake `.env` into an image.
3. Run the lightweight startup preflight.
4. Start the API process or container.
5. Verify `/healthz`.
6. Run fast gate validation in the target package when appropriate.
7. Run full regression before accepting releases or runtime-affecting changes.

Use the [Release Artifact Manifest](release_artifact_manifest.md) as the authoritative include/exclude checklist for source bundles and container images.

## Local Operation

From the `backend` directory:

```powershell
py -3.12 -m venv l8
.\l8\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally and provide the LLM secret when live workflow calls are required:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
ALLOW_REAL_SOURCE_ADAPTERS=false
MEMORY_MAX_RECORD_COUNT=500
```

Run startup checks and start the API:

```powershell
.\l8\Scripts\python.exe scripts\startup_preflight.py
.\l8\Scripts\python.exe main.py
```

Verify readiness:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
```

Expected body:

```json
{
  "status": "ok",
  "service": "grounded-ecommerce-creative-agent",
  "stable_baseline": "l9_9_stable"
}
```

The response must also contain an `X-Request-ID` header.

Open the local Product Mode MVP frontend:

```text
http://127.0.0.1:8001/
```

For a stable demo, enter `balsamic_vinegar` or another local grounded slug. Do not use Amazon URLs in Product Mode; use Debug Mode / Amazon Shadow for Amazon source observation.

## Docker Operation

Build:

```powershell
docker build -t grounded-agent-backend .
```

Run with secrets injected at runtime:

```powershell
docker run --rm -p 8001:8001 --env-file .env grounded-agent-backend
```

The image starts:

```text
uvicorn main:app --host 0.0.0.0 --port 8001
```

Use `/healthz` for container health polling. For full image-content checks, secret exclusion, asset presence and optional container-level validation, execute the [Docker Smoke Protocol](docker_smoke_protocol.md).

## Startup Preflight

Run before a packaged process is accepted for startup:

```powershell
.\l8\Scripts\python.exe scripts\startup_preflight.py
```

In a container:

```powershell
python scripts/startup_preflight.py
```

The script emits JSON and exits non-zero only for hard startup packaging failures:

- `data/reviews/` missing or fewer than ten local datasets.
- `runs/baselines/l9_9_stable/` missing.
- `requirements.txt` or `.env.example` missing.
- `MEMORY_MAX_RECORD_COUNT` not parseable as a positive integer.

`OPENAI_API_KEY` absence is reported but does not fail startup preflight, because health checks and fast validation do not require live LLM access.

## Validation Gates

### Fast Gate

Run after packaging or API-boundary changes and before every release candidate:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py --fast
```

The fast gate covers compilation, contracts, endpoint smoke tests, request ID/logging boundaries, startup/health checks, failure guards and routing checks without live model calls.

### Full Regression

Run before a release, after changes affecting core runtime behavior, and after any source/memory/cost policy change:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py
```

This requires configured LLM credentials and runs the ten-category grounded suite. Review:

- `runs/latest/regression_summary.csv`
- `runs/latest/telemetry_node_aggregate.csv`
- `runs/latest/cost_gate_summary.csv`
- `runs/latest/regression_report.md`

## API And Observability Boundaries

| Surface | Allowed Content |
| --- | --- |
| `/api/v1/generate-copilot` | Product result only. It receives an `X-Request-ID` response header, but the body must not contain `request_id` or `telemetry_summary`. |
| `/api/v1/debug-copilot` | Diagnostic state, `request_id`, raw telemetry, safe `telemetry_summary` and memory observability. |
| `/api/v1/debug-source-probe` | Debug-only real-source shell status and `request_id`; never memory-writing and never executing local/mock anchors. |
| `/healthz` | Static readiness metadata and response header request ID only. |

Structured JSON logs are correlated using `request_id` and may include endpoint, status, latency, goal, product category and source-probe aggregate status. They must not include API keys, complete prompts, full evidence quotations or raw state.

## Storage And Persistence

### Memory Records

`storage/memory_records.json` contains bounded learned outcomes:

- Local development: may persist locally; do not treat mutable local memory as a committed baseline artifact.
- Staging: persist only when testing ongoing memory behavior and retain a documented reset/reseed path.
- Production: mount durable, backed-up storage when persistent memory is enabled; do not rely on ephemeral container disk.

The capacity boundary defaults to:

```dotenv
MEMORY_MAX_RECORD_COUNT=500
```

Monitor retained count, remaining capacity and pruning through debug/telemetry surfaces.

### FAISS And Embedding Cache

FAISS is the preferred retrieval backend when its dependencies and embedding assets are available. For staging or production where persistent semantic memory is required:

- Mount durable storage for FAISS state and required cache assets.
- Monitor backend state and fallback counts.
- Do not bake mutable `storage/faiss_memory/` into the Docker image.

Manual backend diagnosis:

```powershell
.\l8\Scripts\python.exe scripts\check_faiss_backend.py
```

## JSON Fallback Decision

`backend=json_fallback` is an observable degraded mode, not an invisible success.

It is acceptable only when:

- The environment is known to restrict FAISS or embedding/cache availability.
- `faiss_error` is non-empty and recorded in diagnostics/telemetry.
- Fast gate succeeds and the relevant release validation has not exposed memory-quality failure.
- The release owner explicitly records the degradation.

It is a blocker when:

- Production requires persistent semantic memory but the fallback is unexpected or uninvestigated.
- `faiss_error` is absent.
- Fallback accompanies failed nodes, quality-gate failure or memory corruption concerns.

## Accepted Warnings Versus Hard Blockers

Accepted warnings are visible drift that remains inside approved hard boundaries, for example:

- A `grounded_ctr` decrease relative to baseline while still remaining `>= 0.04`.
- Total latency above the warning threshold but below the hard failure threshold.
- A documented constrained-environment JSON fallback with visible `faiss_error`.

Hard blockers include:

- Any absolute grounded quality failure.
- A hard cost-gate failure.
- `failed_nodes` not `None`.
- Fast or full gate failure.
- Product API leaking internal debug or telemetry fields.
- Unexpected or unexplained persistent-memory backend failure.

## Troubleshooting

| Symptom | Diagnosis | Response |
| --- | --- | --- |
| `OPENAI_API_KEY` missing | Startup preflight may still pass, but live workflow/full regression cannot run. | Inject the secret via `.env`, container environment or secret manager; rerun only the live validation that required it. |
| FAISS import fails | Vector backend is unavailable; JSON fallback may be reported. | Run `scripts/check_faiss_backend.py`, validate dependency/cache installation and record `faiss_error`; block production when fallback is not approved. |
| `startup_preflight.py` fails | Required package/data/baseline/config asset is missing or invalid. | Fix the reported `required_failures` before starting or promoting the service. |
| `/healthz` fails | API process/container is not serving its lightweight readiness surface. | Check process/container logs, port mapping and startup errors before making product requests. |
| Fast gate fails | API contracts, boundary guards or deterministic safety tests regressed. | Do not deploy or freeze a baseline; inspect the failing unit/script and restore the boundary. |
| Full regression fails | Grounded quality, live execution, cost or source/memory behavior regressed. | Inspect latest reports and do not release until a passing full run is accepted. |
| Cost gate fails | Token, latency hard limit or failed-node condition exceeded budget. | Treat as blocker; identify hotspot node in telemetry reports before considering a new release. |
| `failed_nodes` is not `None` | At least one runtime node failed during regression. | Treat as blocker regardless of apparent product output quality. |
| Product API exposes debug fields | Product/debug boundary has regressed. | Treat as blocker; product body must not contain `data.debug`, `request_id` or `telemetry_summary`. |

## Release Handoff Checklist

Before production handoff:

1. Execute all commands in the [Release Checklist](release_checklist.md).
2. Verify the stable product baseline is `runs/baselines/l9_9_stable/` and the latest accepted handoff snapshot is `runs/baselines/l10_4_production_handoff/`, or explicitly document newer accepted artifacts.
3. Confirm Docker smoke validation has been completed in a Docker-enabled environment; the current handoff was validated by the GitHub Actions **L10 Manual Docker Smoke** workflow.
4. Confirm memory and FAISS storage mounts follow the environment matrix.
5. Record accepted warnings and all structured-log/request-correlation expectations in the handoff notes.

## Related Documents

- [README](../README.md): quick start and endpoint overview.
- [Deployment Environment Matrix](deployment_environment_matrix.md): environment-specific policy.
- [Docker Smoke Protocol](docker_smoke_protocol.md): container validation procedure.
- [Docker Runtime Smoke Validation Record](docker_runtime_smoke_pending.md): completed CI smoke validation and reusable Docker-enabled execution commands.
- [Regression Protocol](regression_protocol.md): quality and cost gates.
- [Release Checklist](release_checklist.md): release sign-off checklist.
- [Architecture Map](architecture_map.md): module and boundary reference.
- [API Examples](api_examples.md): endpoint requests and response surfaces.
- [Public Demo Quickstart](public_demo_quickstart.md): public Product Mode demo URL, stable inputs and troubleshooting.
- [Public Demo Smoke Checklist](public_demo_smoke_checklist.md): pre-demo Render warmup and Product Mode readiness checks.
- [Release Artifact Manifest](release_artifact_manifest.md): package contents, exclusions and durable-runtime state policy.
- [L10.4 Production Handoff Release Notes](release_notes_l10_4_production_handoff.md): latest validated handoff baseline, costs, memory status and Docker smoke boundary.
- [L10.10 Amazon Shadow Observability Release Notes](release_notes_l10_10_amazon_shadow_observability.md): debug-only Amazon probe, shadow evaluation and observability status.
- [L11.0 Product Mode MVP Release Notes](release_notes_l11_0_product_mode_mvp.md): static frontend serving, Product Mode UX cleanup and browser demo validation.
- [L11.4 Public Demo Polish Release Notes](release_notes_l11_4_public_demo_polish.md): public landing copy, result readability and translation button status.
- [L11.4 Public Demo Final Release Notes](release_notes_l11_4_public_demo_final.md): final public demo polish, Render hardening and translation smoke status.
- [Public Demo Polish Final Audit](public_demo_polish_final_audit.md): final audit for public Product Mode, translation and Product/Debug boundary status.
- [Commercial MVP Scope](commercial_mvp_scope.md): target users, beachhead segment, pricing hypotheses and commercial roadmap.
- [Deployment Provider Decision](deployment_provider_decision.md): Render/Railway/Fly.io/DigitalOcean/AWS Lightsail comparison and recommended MVP deployment path.
- [Render Deployment Setup](render_deployment_setup.md): Render Docker Web Service configuration and post-deploy Product Mode smoke checklist.
- [Public Product Mode Handoff Audit](public_product_mode_handoff_audit.md): public Render handoff artifact, boundary and live-recheck notes.
- [Render First Deployment Smoke 2026-05-24](render_first_deployment_smoke_20260524.md): public Render health, static frontend and Product Mode generation smoke results.

## L12.0-B Commercial MVP User Workflow

Status: ready.

Document:

```text
docs/commercial_mvp_user_workflow.md
```

Current workflow:

```text
Open public demo
? select stable demo product
? run Product Mode
? review Evidence / Strategy / Hook / Storyboard / Evaluation
? translate full output or individual sections if needed
? copy Hook / Storyboard / Markdown / Chinese translation
? give feedback
```

Boundary:

```text
Product Mode continues to use 10 stable local grounded slugs.
Amazon URL remains Debug Mode / Amazon Shadow only.
Product API continues not to expose Debug Trace, telemetry_summary, shadow_sources, or memory_observability.
```

## L12.0-C Public Landing Conversion Copy

Status: ready.

Document:

```text
docs/public_landing_conversion_copy.md
```

Recommended landing copy:

```text
Generate TikTok ad hooks and storyboards from ecommerce review pain points.

Pick a stable demo product, generate a grounded creative brief, translate it to Chinese, and copy the hook or storyboard for your next ad test.
```

Boundary:

```text
This is copy planning only.
No runtime behavior changed.
Product Mode continues to use 10 stable local grounded slugs.
Amazon URL remains Debug Mode / Amazon Shadow only.
```

## L12.0-D ??????

Status: ready.

Document: docs/feedback_collection_flow.md

???????????? Google Form ? Tally ???

?????????
?? creative brief ????
???????????????????Amazon URL?Shopify URL???????????CSV ???

???
- ????
- ?? runtime ??
- ?????????
- ??????
- ????????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

## L12.0-E ?????????

Status: ready.

Document: docs/export_local_history_planning.md

?????????

- Download Markdown
- Download JSON
- localStorage recent generations

???

- ????
- ?? runtime ??
- ??????
- ?????
- ?????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

## L12.0-F MVP ?????????

Status: ready.

Document: docs/mvp_workflow_smoke_protocol.md

?????
- Public ?????
- Product Mode ???
- balsamic_vinegar ?? 200
- Copy Hook / Storyboard / Full Markdown ??
- ????????
- ????????
- Product / Debug ????
- Amazon URL ??? Product Mode ????

???
- ??????
- ?? runtime ??
- ?????
- ?????
- ??????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

## L12.0-G Commercial MVP ??????

Status: ready.

Document: docs/commercial_mvp_planning_final_audit.md

???

- L12.0 Commercial MVP planning ???
- ?? beachhead user: Small ecommerce brand owner
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow
- ???????? L12.1 Commercial MVP execution

?????

- Download Markdown / JSON
- localStorage recent generations
- feedback form link
- example gallery
- landing copy UI polish

## L12.1-C Feedback Form Link

Status: ready.

Feedback form:

https://docs.google.com/forms/d/e/1FAIpQLSftwZouinTX8Z_9APPqDKu0zXyQsMXcqqHf7eZXzZft9MyqVA/viewform?usp=dialog

???
- ???????????
- ?????????
- ??????
- ?????
- ?????

## L12.1-D ?????

Status: ready.

Document: docs/example_gallery_planning.md

?????????????

- balsamic_vinegar
- pet_hair_vacuum
- desk_lamp

???
- ????
- ?? runtime ??
- ???????
- ??????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow


## L12.2-B Example Gallery Public Smoke

Status: ready.

Document: docs/example_gallery_public_smoke.md

结果：
- Public 页面可访问
- Example Gallery 可见
- 3 个静态示例卡片可见
- Try This Product 可见
- Feedback 入口可见
- generate-copilot with balsamic_vinegar 返回 200

边界：
- 不改 runtime 行为
- 不新增后端接口
- 不新增数据库
- Product Mode 继续使用 10 个 stable local grounded slug
- Amazon URL 仍然只属于 Debug Mode / Amazon Shadow

## L12.2-C Commercial MVP ????????

Status: ready.

Document: docs/commercial_mvp_execution_final_audit.md

????

- Download Markdown / JSON
- Local recent generations
- Feedback form link
- Static Example Gallery
- Example Gallery public smoke validation

?? Public Demo ????

- ??
- ??
- ??
- ??
- ????
- ????
- ?????

???

- ?????
- ?????
- ??????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

## L12.3-A Public Demo Layout Polish

Status: ready.

?????Hero?????Example Gallery?Product Result?Copy / Download / Translation actions?Recent Generations?Feedback?Debug Mode advanced section?

????? runtime???? API?????????????????Product Mode ???? 10 ? stable slug?Amazon URL ????? Debug Mode / Amazon Shadow?

## L12.3-C Public Demo Commercial Polish ????

Status: ready.

Document: docs/public_demo_commercial_polish_final_audit.md

???

- Public ????
- Product Mode ???
- Example Gallery ??
- Recent Generations ??
- Feedback ??
- Debug Mode ????
- Copy / Download / Translation ??

???

- ?????
- ?????
- ??????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

??????

L12.4 Controlled Amazon primary design

## L12.4-A Controlled Amazon Primary Design

Status: ready.

Document: docs/controlled_amazon_primary_design.md

???

- Amazon URL ??????? Product Mode
- amazon_primary ?????
- ?????????? 10 ? stable local grounded slug
- Amazon URL ??????? controlled beta
- beta ????? shadow / safety / fallback / error classification ??

?????????? runtime?

## L12.4-B Amazon Beta UX Copy

Status: ready.

Document: docs/amazon_beta_ux_copy.md

???

- Amazon URL Beta ??????? experimental
- Stable Product Mode ???? 10 ? demo products
- Amazon URL ?????? fully supported
- ???????????????
- amazon_primary ?????

???????????? runtime?

## L12.4-C Amazon Beta API Contract Design

Status: ready.

Document: docs/amazon_beta_api_contract_design.md

???

- Amazon Beta ???????? endpoint
- ????? /api/v1/generate-copilot
- ???? ENABLE_AMAZON_BETA=false ???? flag
- beta_acknowledged ????? true
- ??????? error
- ?? memory_write_allowed=false

????? contract ????? runtime?

## L12.4-D Amazon Beta Fallback Design

Status: ready.

Document: docs/amazon_beta_fallback_design.md

???

- Amazon Beta ?????? generation
- Amazon Beta ????? memory
- Amazon Beta ??????? Recent Generations
- Amazon Beta ????????? creative brief
- ?????????? stable demo products
- stable Product Mode ????

????? fallback ????? runtime?

## L12.4-E Amazon Beta Evaluation Checklist

Status: ready.

Document: docs/amazon_beta_evaluation_checklist.md

???

- Amazon Beta ??????? shadow / safety / fallback / UI / API contract ??
- blocked / captcha / parse_empty / not_found ???? generation
- ????? memory
- ?????? Recent Generations
- ??????? creative brief
- stable slug Product Mode ????????

???????????? runtime?

## L12.4-F Amazon Beta Implementation Decision

Status: ready.

Document: docs/amazon_beta_implementation_decision.md

???

- ????? Amazon URL Beta
- Amazon URL ???? Debug Mode / Amazon Shadow / future controlled beta
- ?? Product Mode ???? 10 ? stable local grounded slug
- amazon_primary ?????
- ??????? L12.5 Public demo release refresh

???????????? runtime?

## L12.5-A Commercial Demo Release Refresh

Status: ready.

Document: docs/release_notes_l12_commercial_demo.md

?????

- Commercial Demo v1 ready
- Product Mode ???
- Example Gallery ??
- Download Markdown / JSON ??
- Recent Generations ??
- Feedback form link ??
- Full / Section Chinese Translation ??
- Amazon Beta ?????????

???

- ?????
- ?????
- ??????
- Product Mode ???? 10 ? stable local grounded slug
- Amazon URL ????? Debug Mode / Amazon Shadow

## L12.5-B Commercial Demo Final Audit

Status: ready.

Document: docs/commercial_demo_final_audit.md

???

- Commercial Demo v1 ready
- Public Demo ????
- Product Mode ???
- Copy / Download / Translation / Recent Generations / Feedback / Example Gallery ??
- Product / Debug ????
- Amazon URL ????? Debug Mode / Amazon Shadow
- Amazon Beta ?????????

????

L12.5-C Tag commercial-demo-v1

## L12.5-C Commercial Demo v1 Archive

Status: ready.

Document: docs/commercial_demo_v1_archive.md

Tag:

commercial-demo-v1

???

- Commercial Demo v1 ???
- Product Mode ???
- Copy / Download / Translation / Recent Generations / Feedback / Example Gallery ??
- Amazon Beta ?????????
- Product Mode ???? 10 ? stable local grounded slug

## L13.0-A Feedback Collection Launch Checklist

Status: ready.

Document: docs/feedback_collection_launch_checklist.md

?????

- ????????????
- ??????? 5 ? 10 ?????
- ????? 5 ? 25 ?????
- ???????????Amazon URL???????????????

???

- ?? runtime
- ?????
- ?????
- ??????
- ??? Amazon URL Product Mode

## L13.0-B Feedback Response Tracking Plan

Status: ready.

Document: docs/feedback_response_tracking_plan.md

?????

- ???????????????
- ???? 5 ?????
- ???? 10 ? 25 ?????
- ????? docs/feedback_round_1_summary.md

???

- ?? runtime
- ?????????
- ??????
- ?????
- ?????

## L13.0-C Feedback Outreach Plan

Status: ready.

Document: docs/feedback_outreach_plan.md

?????

- ???????????
- ?? 5 ? 10 ?????
- ?????????????????
- ??????? demo???????? feedback form

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.0-D Feedback Launch Smoke Record

Status: ready.

Document: docs/feedback_launch_smoke_record.md

?????

- ?????????????????
- ?? Public Demo
- ?? Product Mode
- ?? Feedback Form
- ?? Product / Debug ??

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.0-E Feedback Outreach Tracker

Status: ready.

Document: docs/feedback_outreach_tracker.md

?????

- ?????????????
- ??? 5 ?
- ?????? demo??????????????
- ??????????????

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.0-F Feedback Round 1 Summary Template

Status: ready.

Document: docs/feedback_round_1_summary_template.md

?????

- ???????????????
- ?????????? docs/feedback_round_1_summary.md
- ?????????? product description input?Amazon Beta???????????????

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.0-G Feedback Collection Launch Final Audit

Status: ready.

Document: docs/feedback_collection_launch_final_audit.md

???

- ???????????????
- ??????? 5 ?????
- Public Demo ? Feedback Form ???
- ????????? docs/feedback_round_1_summary.md

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.1-A Product Description Input Design

Status: ready.

Document: docs/product_description_input_design.md

???

- ????????????? Product Description Mode
- ???? Amazon URL Product Mode
- ?????????????????
- ???????? endpoint?????? stable slug Product Mode

???

- ???????
- ?? runtime
- ??? API
- ??????
- ?????
- ?????

## L13.1-B Product Description API Contract Design

Status: ready.

Document: docs/product_description_api_contract_design.md

???

- ???????? endpoint: POST /api/v1/generate-from-description
- ????? /api/v1/generate-copilot
- source ???? user_provided_description
- ??? Amazon / Source Probe / Amazon Shadow
- ?? memory
- ????? 10 ? stable slug Product Mode

???

- ????? contract ??
- ?? runtime
- ??? API
- ??????
- ?????
- ?????

## L13.1-C Product Description Frontend UX Design

Status: ready.

Document: docs/product_description_frontend_ux_design.md

???

- Product Description Mode ???????????
- ??? stable slug Product Mode
- ?????? Product Result ??
- source ???? user_provided_description
- ??? Amazon / Source Probe / Amazon Shadow

???

- ????? UX ??
- ?? runtime
- ??? API
- ??????
- ?????
- ?????

## L13.1-F Product Description Mode Smoke

Status: ready.

Document: docs/product_description_mode_smoke.md

???

- Product Description Mode ?????
- /api/v1/generate-from-description ??
- source=user_provided_description
- Copy / Download / Translation / Recent Generations ????
- Product / Debug ????

???

- ??? Amazon
- ??? Source Probe
- ??? Amazon Shadow
- ??? data.debug
- ??? telemetry_summary / shadow_sources / memory_observability

## L13.1-G Product Description Mode Release Notes

Status: ready.

Document: docs/release_notes_l13_1_product_description_mode.md

???

- Product Description Mode ?? endpoint ???
- Product Description Mode ?????
- /api/v1/generate-from-description ??
- source=user_provided_description
- Copy / Download / Translation / Recent Generations ????
- Stable slug Product Mode ????
- Product / Debug ????

???

- ??? Amazon
- ??? Source Probe
- ??? Amazon Shadow
- ??? telemetry_summary / shadow_sources / memory_observability
- Amazon URL ??? stable Product Mode input

## L13.1-H Product Description Mode Final Audit

Status: ready.

Document: docs/product_description_mode_final_audit.md

???

- Product Description Mode v1 ready
- /api/v1/generate-from-description ??
- ?? Product Description Mode ??
- source=user_provided_description
- Copy / Download / Translation / Recent Generations ????
- Stable slug Product Mode ????
- Product / Debug ????

????

L13.1-I Tag product-description-demo-v1

## L13.1-I Product Description Demo v1 Archive

Status: ready.

Document: docs/product_description_demo_v1_archive.md

Tag:

product-description-demo-v1

???

- Product Description Mode v1 ???
- /api/v1/generate-from-description ??
- ?? Product Description Mode ??
- source=user_provided_description
- Copy / Download / Translation / Recent Generations ??
- Stable slug Product Mode ????
- Product / Debug ????

## L13.2-A Product Description Trial Launch Checklist

Status: ready.

Document: docs/product_description_trial_launch_checklist.md

?????

- ????????? Product Description Mode
- ?????????????????????
- ??????????? stable slug ????
- ????? docs/product_description_trial_round_1_summary.md

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.2-B Product Description Trial Outreach Tracker

Status: ready.

Document: docs/product_description_trial_outreach_tracker.md

?????

- ?? Product Description Mode ??????????
- ?? 5 ?????
- ?????? Product Description Mode??????????????
- ?????????????????Product Description polish?Amazon Beta ? pricing / waitlist

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.2-C Product Description Trial Smoke Record

Status: ready.

Document: docs/product_description_trial_smoke_record.md

?????

- ?? Product Description Mode ???????? smoke ???
- ?? Public Demo
- ?? Generate from description
- ?? source=user_provided_description
- ?? Copy / Download / Translation / Recent Generations
- ?? Product / Debug ??

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.2-D Product Description Trial Round 1 Summary Template

Status: ready.

Document: docs/product_description_trial_round_1_summary_template.md

?????

- ?? Product Description Mode ?????????
- ?????????? docs/product_description_trial_round_1_summary.md
- ???????????????Product Description polish?Amazon Beta?pricing / waitlist ? onboarding

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.2-E Product Description Trial Launch Final Audit

Status: ready.

Document: docs/product_description_trial_launch_final_audit.md

???

- Product Description Mode ?????????????
- ????? 5 ?????
- ????????????????? customer pain points
- ????????? docs/product_description_trial_round_1_summary.md

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.3-A Pricing / Waitlist Design

Status: ready.

Document: docs/pricing_waitlist_design.md

???

- ???? waitlist????? payment
- Pricing ??? Free Demo?Starter?Creator / Operator?Agency
- Stripe / login / subscription ????
- ?????? waitlist ?????????????????

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.3-B Waitlist Form Design

Status: ready.

Document: docs/waitlist_form_design.md

???

- Waitlist ??????? Google Form
- ??? email???????????????????????? beta ??
- ???? login / payment / Stripe / database

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.3-D Waitlist Link Integration

Status: ready.

Waitlist form:

https://docs.google.com/forms/d/e/1FAIpQLSd5rBYj_42J8gJ1n1deEl0ePySMKe6yaZ8K0gIvSt62QgsSnQ/viewform?usp=publish-editor

???
- Public Demo ???? Join waitlist
- README ?? waitlist link
- quickstart ?? waitlist link
- smoke checklist ?? waitlist link

???
- ???????
- ??????
- ?????
- ?????

## L13.3-E Pricing Validation Checklist

Status: ready.

Document: docs/pricing_validation_checklist.md

???

- ????? pricing / waitlist ??
- ??? Stripe / login / subscription
- ?? waitlist ?????????????? payment
- ???????? Product Description polish?Amazon Beta?Shopify input?Pasted reviews input ? Starter plan

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.3-F Pricing / Waitlist Final Audit

Status: ready.

Document: docs/pricing_waitlist_final_audit.md

???

- Waitlist ?????? Public Demo
- ???? payment / Stripe / login / subscription
- ??????????? email??? beta???????
- ?? waitlist ?????????????? payment
- ??????? L13.4 Product Description Mode polish planning

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.4-A Product Description Mode Polish Planning

Status: ready.

Document: docs/product_description_mode_polish_planning.md

???

- Product Description Mode ??????????
- ???? product description / customer pain points ??????? placeholder
- ?????? helper copy?sample input?frontend polish

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.4-B Product Description Helper Copy

Status: ready.

Document: docs/product_description_helper_copy.md

???

- Product Description Mode ??????????
- ???? product description ? customer pain points ???
- source ????? user_provided_description
- ???? Amazon review / scraped reviews / verified customer reviews

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.4-C Product Description Sample Input Design

Status: ready.

Document: docs/product_description_sample_input_design.md

???

- Product Description Mode ???? Use sample product ??
- ?????? Portable mini blender
- ?????????????????? API
- ??? Debug Mode / Source Probe / Amazon Shadow
- ??? Recent Generations

???

- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.4-E Product Description Polish Smoke Record

Status: ready.

Document: docs/product_description_polish_smoke_record.md

???

- Product Description helper text ??
- Good inputs include ??
- Use sample product ??
- Use sample product ???????????? API
- Frontend boundary test PASS
- Fast gate PASS?123 tests

???

- ??? Amazon
- ??? Source Probe
- ??? Amazon Shadow
- ??? data.debug
- ??? telemetry_summary / shadow_sources / memory_observability

## L13.4-F Product Description Polish Release Notes

Status: ready.

Document: docs/release_notes_l13_4_product_description_polish.md

???

- Product Description Mode ????????
- helper text ??
- Good inputs include ??
- Use sample product ??
- Use sample product ???????????? API
- Frontend boundary test PASS
- Fast gate PASS?123 tests

???

- ??? Amazon
- ??? Source Probe
- ??? Amazon Shadow
- ??? data.debug
- ??? telemetry_summary / shadow_sources / memory_observability

????

L13.4-G Product Description polish final audit

## L13.4-G Product Description Polish Final Audit

Status: ready.

Document: docs/product_description_polish_final_audit.md

???

- Product Description Mode ???????????
- helper text / Good inputs include / Use sample product ???
- Use sample product ???????????? API
- Frontend boundary test PASS
- Fast gate PASS?123 tests
- Product / Debug ????

????

L13.5 Public demo refresh for product-description-demo-v1

## L13.5-A Public Demo Refresh for Product Description Demo v1

Status: ready.

Document: docs/public_demo_refresh_l13_5_product_description.md

???

- Public Demo ?????
- Product Description Mode ??
- Use sample product / Good inputs include ??
- /api/v1/generate-from-description ????
- source=user_provided_description
- Feedback / Waitlist ??
- Product / Debug ????

???

Product Description Demo v1 ????????????

## L13.5-B Public Demo Refresh Final Audit

Status: ready.

Document: docs/public_demo_refresh_final_audit.md

???

- Public Demo refresh ???
- Product Description Mode ????
- Use sample product / Good inputs include ??
- /api/v1/generate-from-description ????
- source=user_provided_description ???
- Feedback / Waitlist ??
- Product / Debug ????

???

Product Description Demo v1 polish ??????????????

## L13.5-C Product Description Polish v1 Archive

Status: ready.

Document: docs/product_description_polish_v1_archive.md

Tag:

product-description-polish-v1

???

- Product Description Polish v1 ???
- Public Demo refresh ???
- Product Description Mode ????
- Use sample product / Good inputs include ??
- Feedback / Waitlist ??
- Product / Debug ????
- ?????????

## L13.6-A Language Mode Design

Status: ready.

Document: docs/language_mode_design.md

???

- ????? Language Mode
- ?????? English ? ??
- ?? English
- ??????? UI ??????????
- ???? output_language ??
- ???? /api/v1/generate-copilot ? /api/v1/generate-from-description

???

- ???????
- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.6-B Language Mode API Contract

Status: ready.

Document: docs/language_mode_api_contract.md

???

- Language Mode ???? output_language ??
- ???? en / zh-CN
- ?? en
- ???? /api/v1/generate-copilot ? /api/v1/generate-from-description
- ???????????????
- Product / Debug ????

???

- ????? contract ??
- ?? runtime
- ???????
- ??????
- ?????
- ?????

## L13.6-C Language Mode Frontend Copy Map

Status: ready.

Document: docs/language_mode_frontend_copy_map.md

???

- Language Mode ?????????????
- English / ?? selector ?????
- Product Description Mode?Result?Actions?Recent Generations?Feedback?Waitlist?Debug Mode ?????
- ?????????? UI ??????

???

- ????? copy map
- ?? runtime
- ???????
- ??????
- ?????
- ?????

