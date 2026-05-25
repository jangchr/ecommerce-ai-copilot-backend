# Grounded Ecommerce Creative Agent Backend

This backend is an evidence-driven ecommerce creative agent runtime. It turns grounded product-review evidence and trend context into structured strategy, executable short-video scene graphs, reward evaluation, reflection routing and bounded memory. Local curated review datasets remain the stable regression anchor while external source adapters stay feature-flagged and safely degradable.

Current Product Mode actions include a static **Example Gallery**, copy controls, full and section-level Chinese translation, client-side **Download Markdown** / **Download JSON** exports, and browser-local **Recent Generations** for user-visible creative briefs.

## Documentation Map

- [Architecture Map](docs/architecture_map.md): backend modules, workflow data flow and safety boundaries.
- [Regression Protocol](docs/regression_protocol.md): quality thresholds, reports, memory health and cost gates.
- [API Examples](docs/api_examples.md): request examples and product/debug response boundaries.
- [Frontend Smoke Protocol](docs/frontend_smoke_protocol.md): manual Debug Mode and UI/API boundary checks.
- [Product Mode Demo Protocol](docs/product_mode_demo_protocol.md): local demo flow for stable grounded slugs and copy controls.
- [Public Demo Quickstart](docs/public_demo_quickstart.md): public Product Mode demo URL, stable inputs and troubleshooting.
- [Public Demo Smoke Checklist](docs/public_demo_smoke_checklist.md): pre-demo public uptime, cold-start and warmup checks.
- [Release Checklist](docs/release_checklist.md): required preflight commands and release blockers.
- [Deployment Environment Matrix](docs/deployment_environment_matrix.md): per-environment secrets, storage, cache, probe and artifact policies.
- [Production Handoff Runbook](docs/production_handoff_runbook.md): operational startup, validation, persistence and troubleshooting guidance.
- [Release Artifact Manifest](docs/release_artifact_manifest.md): required package contents, exclusions and runtime persistence boundaries.
- [Render Deployment Setup](docs/render_deployment_setup.md): Render Docker Web Service configuration, secrets, health checks and Product Mode smoke checklist.
- [Render First Deployment Smoke](docs/render_first_deployment_smoke_20260524.md): public Render health, static frontend and Product Mode generation smoke results.
- [L10.10 Amazon Shadow Observability Release Notes](docs/release_notes_l10_10_amazon_shadow_observability.md): debug-only Amazon probe, shadow evaluation and observability status.
- [L11.0 Product Mode MVP Release Notes](docs/release_notes_l11_0_product_mode_mvp.md): static frontend serving, Product Mode UX cleanup and browser demo validation.
- [L11.4 Public Demo Polish Release Notes](docs/release_notes_l11_4_public_demo_polish.md): public landing copy, result readability and translation button status.
- [L11.4 Public Demo Final Release Notes](docs/release_notes_l11_4_public_demo_final.md): final public demo polish, Render hardening and translation smoke status.
- [Public Demo Polish Final Audit](docs/public_demo_polish_final_audit.md): final audit for public Product Mode, translation and Product/Debug boundary status.
- [Public Demo v1 Archive](docs/public_demo_v1_archive.md): archived public demo v1 snapshot at commit `81aeffa`.
- [Commercial MVP Scope](docs/commercial_mvp_scope.md): target users, beachhead segment, pricing hypotheses and commercial roadmap.
- [Commercial MVP User Workflow](docs/commercial_mvp_user_workflow.md) ? L12.0-B user workflow from public demo entry to generation, translation, copy actions, and feedback.
- [Public Landing Conversion Copy](docs/public_landing_conversion_copy.md) ? L12.0-C landing-page copy for commercial MVP conversion.
- [Feedback Collection Flow](docs/feedback_collection_flow.md) ? L12.0-D ??????????????
- [Example Gallery Planning](docs/example_gallery_planning.md) ? L12.1-D ??????
- [Export and Local History Planning](docs/export_local_history_planning.md) ? L12.0-E ???????????????
- [MVP Workflow Smoke Protocol](docs/mvp_workflow_smoke_protocol.md) ? L12.0-F Public Demo ? Commercial MVP ???????????
- [Commercial MVP Planning Final Audit](docs/commercial_mvp_planning_final_audit.md) ? L12.0-G Commercial MVP ???????
- [Commercial MVP User Workflow](docs/commercial_mvp_user_workflow.md) — L12.0-B user workflow from public demo entry to generation, translation, copy actions, and feedback.

## Runtime

- Verified local development environment: **Python 3.12**.
- For production migration, select and pin one supported Python line, preferably **3.11 or 3.12**, across development, CI and deployment.

## Setup On Windows

From the `backend` directory:

```powershell
py -3.12 -m venv l8
.\l8\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally and set `OPENAI_API_KEY`. Do not commit real secrets.

The safe default source configuration uses the local grounded review dataset and mock trend adapter:

```dotenv
ALLOW_REAL_SOURCE_ADAPTERS=false
```

## Start The API

```powershell
.\l8\Scripts\python.exe main.py
```

The development API listens on `http://127.0.0.1:8001`. Interactive FastAPI documentation is available at `/docs`.

Public Product Mode demo:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

For the local Product Mode MVP demo, start the backend and open the served frontend:

```powershell
.\l8\Scripts\python.exe main.py
```

```text
http://127.0.0.1:8001/
```

Use the 10 stable local grounded slugs, starting with `balsamic_vinegar`. Amazon URLs remain Debug Mode / Amazon Shadow inputs, not the stable Product Mode path.

Verify the lightweight deployment health probe after startup:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
```

Expected response:

```json
{
  "status": "ok",
  "service": "grounded-ecommerce-creative-agent",
  "stable_baseline": "l9_9_stable"
}
```

## Docker Packaging

Build the backend image from this directory:

```powershell
docker build -t grounded-agent-backend .
```

Run the container with local environment variables injected at runtime:

```powershell
docker run --rm -p 8001:8001 --env-file .env grounded-agent-backend
```

The image does not copy `.env`; live workflow requests still require `OPENAI_API_KEY` to be supplied through `--env-file` or your deployment secret manager. The safe default remains `ALLOW_REAL_SOURCE_ADAPTERS=false`.

Verify container readiness through the lightweight health endpoint:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
```

The container includes `data/reviews/` and frozen `runs/baselines/` assets so local grounded anchors and release comparison artifacts remain available. It excludes mutable latest/history run output and runtime FAISS indexes from the build context.

For image-content checks, optional in-container fast regression and health verification steps, follow the [Docker Smoke Protocol](docs/docker_smoke_protocol.md).

## Environment Diagnostics

Run the lightweight startup preflight before starting a packaged or containerized service:

```powershell
.\l8\Scripts\python.exe scripts\startup_preflight.py
```

Inside the Docker image, use:

```powershell
python scripts/startup_preflight.py
```

This check validates packaged data, the stable baseline and bounded-memory configuration without running the workflow, calling an LLM or requiring `OPENAI_API_KEY`.

Run the required environment preflight:

```powershell
.\l8\Scripts\python.exe scripts\check_env.py
```

Run the manual FAISS backend diagnostic when dependencies, embedding caches or execution permissions change:

```powershell
.\l8\Scripts\python.exe scripts\check_faiss_backend.py
```

When FAISS is available, the expected diagnostic state is `backend=faiss` and `fallback_count=0`. A visible `json_fallback` with `faiss_error` is an observable degradation path for constrained environments.

## Regression Gates

Use the fast gate during ordinary development. It runs compilation, unit checks, API smoke checks, failure checks and routing checks without live LLM regression calls:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py --fast
```

Run the full grounded regression after core workflow, prompt, reward, memory or source-runtime changes. It requires configured LLM credentials and executes the ten-category grounded suite:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py
```

Freeze an accepted full-run baseline without overwriting an existing milestone:

```powershell
.\l8\Scripts\python.exe scripts\freeze_baseline.py --name <name>
```

The current stable release baseline is:

```text
runs/baselines/l9_9_stable/
```

The latest accepted production handoff baseline is:

```text
runs/baselines/l10_4_production_handoff/
```

The current Product Mode MVP baseline is:

```text
runs/baselines/l11_0_product_mode_mvp/
```

Historical stable milestone:

```text
runs/baselines/l9_6_f_faiss_recovery/
```

Release candidate predecessor:

```text
runs/baselines/l9_9_rc1/
```

For quality thresholds, cost gates, memory health fields and baseline handling, see the [Regression Protocol](docs/regression_protocol.md).

## API Endpoints

### Health Check

```text
GET /healthz
```

Returns lightweight deployment readiness metadata. It does not run the workflow, call an LLM or invoke source adapters.

### Product API

```text
POST /api/v1/generate-copilot
```

Returns the product-facing creative result: insights, audience, strategy, assets, evaluation and feedback. It does not expose internal debug state.

### Debug API

```text
POST /api/v1/debug-copilot
```

Returns regression and observability fields, including evidence, cognitive/execution state, world metrics, telemetry, memory observability, regeneration state and revision count.

### Debug-Only Source Probe API

```text
POST /api/v1/debug-source-probe
```

Inspects the disabled real-source adapter shells without entering the product workflow or writing memory. It never executes the local/mock regression anchors through the probe surface.

Request and response surfaces are validated by Pydantic models in `schemas/api_contract.py` and `schemas/source_probe_contract.py`. See [API Examples](docs/api_examples.md) for request recipes and the [Frontend Smoke Protocol](docs/frontend_smoke_protocol.md) for debugger behavior.

## Regression Reports

Full regression output follows this retention convention:

| Directory | Contents |
| --- | --- |
| `runs/latest/` | Latest full regression reports and per-category results |
| `runs/history/<timestamp>/` | Archived full-run outputs |
| `runs/baselines/` | Manually frozen accepted baselines |

Typical generated reports include:

- `regression_summary.csv`
- `telemetry_summary.csv`
- `telemetry_node_aggregate.csv`
- `cost_gate_summary.csv`
- `regression_report.md`

## Stable Baseline Status

Current stable release:

```text
L9.9-Stable final release baseline
runs/baselines/l9_9_stable/
```

Latest production handoff validation baseline:

```text
L10.4 production handoff baseline
runs/baselines/l10_4_production_handoff/
```

Product Mode MVP baseline:

```text
L11.0 Product Mode MVP baseline
runs/baselines/l11_0_product_mode_mvp/
```

Historical milestones:

```text
L9.6 FAISS recovery + stochastic diff gate baseline
runs/baselines/l9_6_f_faiss_recovery/

L9.9-RC1 release candidate baseline
runs/baselines/l9_9_rc1/
```

Stable release details are recorded in [docs/release_notes_l9_9_stable.md](docs/release_notes_l9_9_stable.md). The preceding candidate remains documented in [docs/release_notes_l9_9_rc1.md](docs/release_notes_l9_9_rc1.md).
Production handoff validation details are recorded in [docs/release_notes_l10_4_production_handoff.md](docs/release_notes_l10_4_production_handoff.md).
Amazon shadow-source observability details are recorded in [docs/release_notes_l10_10_amazon_shadow_observability.md](docs/release_notes_l10_10_amazon_shadow_observability.md).
Product Mode MVP details are recorded in [docs/release_notes_l11_0_product_mode_mvp.md](docs/release_notes_l11_0_product_mode_mvp.md).
Public demo polish details are recorded in [docs/release_notes_l11_4_public_demo_polish.md](docs/release_notes_l11_4_public_demo_polish.md).
Final public demo polish release details are recorded in [docs/release_notes_l11_4_public_demo_final.md](docs/release_notes_l11_4_public_demo_final.md), with audit results in [docs/public_demo_polish_final_audit.md](docs/public_demo_polish_final_audit.md).
Public Demo v1 is archived at commit `81aeffa` and documented in [docs/public_demo_v1_archive.md](docs/public_demo_v1_archive.md).

The runtime is currently packaged around grounded local datasets, observable memory/FAISS behavior, protected product/debug API boundaries and fast/full regression gates.

- Feedback form: https://docs.google.com/forms/d/e/1FAIpQLSftwZouinTX8Z_9APPqDKu0zXyQsMXcqqHf7eZXzZft9MyqVA/viewform?usp=dialog

- [Example Gallery Public Smoke](docs/example_gallery_public_smoke.md) — L12.2-B 示例库公网验证。
- [Commercial MVP Execution Final Audit](docs/commercial_mvp_execution_final_audit.md) ? L12.2-C Commercial MVP ?????????

- L12.3-A Public demo layout polish ? ??????? Hero?????Example Gallery?????????Recent Generations?Feedback?Debug ????
- [Public Demo Commercial Polish Final Audit](docs/public_demo_commercial_polish_final_audit.md) ? L12.3-C Public Demo ??????????
- [Controlled Amazon Primary Design](docs/controlled_amazon_primary_design.md) ? L12.4-A ?? Amazon URL beta ???
- [Amazon Beta UX Copy](docs/amazon_beta_ux_copy.md) ? L12.4-B Amazon URL Beta ?????
- [Amazon Beta API Contract Design](docs/amazon_beta_api_contract_design.md) ? L12.4-C Amazon URL Beta API contract ???
- [Amazon Beta Fallback Design](docs/amazon_beta_fallback_design.md) ? L12.4-D Amazon URL Beta ???????
- [Amazon Beta Evaluation Checklist](docs/amazon_beta_evaluation_checklist.md) ? L12.4-E Amazon URL Beta ????????
- [Amazon Beta Implementation Decision](docs/amazon_beta_implementation_decision.md) ? L12.4-F Amazon URL Beta ???????????
- [L12 Commercial Demo Release Notes](docs/release_notes_l12_commercial_demo.md) ? Commercial Demo v1 release notes?
- [Commercial Demo Final Audit](docs/commercial_demo_final_audit.md) ? L12.5-B Commercial Demo v1 ?????
- [Commercial Demo v1 Archive](docs/commercial_demo_v1_archive.md) ? commercial-demo-v1 ?????
- [Feedback Collection Launch Checklist](docs/feedback_collection_launch_checklist.md) ? L13.0-A ?????????????
- [Feedback Response Tracking Plan](docs/feedback_response_tracking_plan.md) ? L13.0-B ????????????????
- [Feedback Outreach Plan](docs/feedback_outreach_plan.md) ? L13.0-C ?????????????????
- [Feedback Launch Smoke Record](docs/feedback_launch_smoke_record.md) ? L13.0-D ????????????
- [Feedback Outreach Tracker](docs/feedback_outreach_tracker.md) ? L13.0-E ???????????????
- [Feedback Round 1 Summary Template](docs/feedback_round_1_summary_template.md) ? L13.0-F ??????????????
- [Feedback Collection Launch Final Audit](docs/feedback_collection_launch_final_audit.md) ? L13.0-G ???????????
- [Product Description Input Design](docs/product_description_input_design.md) ? L13.1-A ?????????
