# Grounded Ecommerce Creative Agent Backend

This backend is an evidence-driven ecommerce creative agent runtime. It turns grounded product-review evidence and trend context into structured strategy, executable short-video scene graphs, reward evaluation, reflection routing and bounded memory. Local curated review datasets remain the stable regression anchor while external source adapters stay feature-flagged and safely degradable.

Current Product Mode actions include stable slug generation, **Product Description Mode**, a static **Example Gallery**, copy controls, full and section-level Chinese translation, client-side **Download Markdown** / **Download JSON** exports, and browser-local **Recent Generations** for user-visible creative briefs.

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
- [Product Description API Contract Design](docs/product_description_api_contract_design.md): L13.1-D Product Description Mode backend endpoint contract and safety boundary.
- [Feedback Collection Flow](docs/feedback_collection_flow.md) ? L12.0-D ??????????????
- [Example Gallery Planning](docs/example_gallery_planning.md) ? L12.1-D ??????
- [Export and Local History Planning](docs/export_local_history_planning.md) ? L12.0-E ???????????????
- [MVP Workflow Smoke Protocol](docs/mvp_workflow_smoke_protocol.md) ? L12.0-F Public Demo ? Commercial MVP ???????????
- [Commercial MVP Planning Final Audit](docs/commercial_mvp_planning_final_audit.md) ? L12.0-G Commercial MVP ???????
- [Commercial MVP User Workflow](docs/commercial_mvp_user_workflow.md) — L12.0-B user workflow from public demo entry to generation, translation, copy actions, and feedback.

## MVP Preview Freeze

- [MVP Preview Freeze](docs/mvp-preview-freeze.md): final CrossGrowth MVP Preview Freeze status, gate results, scope, limitations, and safety boundaries.
- [Post-MVP Unlock Plan](docs/post-mvp-unlock-plan.md): Phase 2 capability gates for future real LLM, provider, persistence, export, upload, policy, task, token, external call, and audit work.

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
- [Product Description API Contract Design](docs/product_description_api_contract_design.md) ? L13.1-B ?????? API contract ???
- [Product Description Frontend UX Design](docs/product_description_frontend_ux_design.md) ? L13.1-C ???????? UX ???
- [Product Description Mode Smoke](docs/product_description_mode_smoke.md) ? L13.1-F ???????? smoke ???
- [L13.1 Product Description Mode Release Notes](docs/release_notes_l13_1_product_description_mode.md) ? Product Description Mode release notes?
- [Product Description Mode Final Audit](docs/product_description_mode_final_audit.md) ? L13.1-H Product Description Mode ?????
- [Product Description Demo v1 Archive](docs/product_description_demo_v1_archive.md) ? product-description-demo-v1 ?????
- [Product Description Trial Launch Checklist](docs/product_description_trial_launch_checklist.md) ? L13.2-A ?????????????????
- [Product Description Trial Outreach Tracker](docs/product_description_trial_outreach_tracker.md) ? L13.2-B ??????????????????
- [Product Description Trial Smoke Record](docs/product_description_trial_smoke_record.md) ? L13.2-C ????????? smoke ???
- [Product Description Trial Round 1 Summary Template](docs/product_description_trial_round_1_summary_template.md) ? L13.2-D ????????????????
- [Product Description Trial Launch Final Audit](docs/product_description_trial_launch_final_audit.md) ? L13.2-E ???????????????
- [Pricing / Waitlist Design](docs/pricing_waitlist_design.md) ? L13.3-A pricing ? waitlist ???
- [Waitlist Form Design](docs/waitlist_form_design.md) ? L13.3-B waitlist ?????
- Waitlist form: https://docs.google.com/forms/d/e/1FAIpQLSd5rBYj_42J8gJ1n1deEl0ePySMKe6yaZ8K0gIvSt62QgsSnQ/viewform?usp=publish-editor
- [Pricing Validation Checklist](docs/pricing_validation_checklist.md) ? L13.3-E pricing ?????
- [Pricing / Waitlist Final Audit](docs/pricing_waitlist_final_audit.md) ? L13.3-F pricing / waitlist ?????
- [Product Description Mode Polish Planning](docs/product_description_mode_polish_planning.md) ? L13.4-A ?????????????
- [Product Description Helper Copy](docs/product_description_helper_copy.md) ? L13.4-B ???????????
- [Product Description Sample Input Design](docs/product_description_sample_input_design.md) ? L13.4-C ???????????
- [Product Description Polish Smoke Record](docs/product_description_polish_smoke_record.md) ? L13.4-E ???????? smoke ???
- [L13.4 Product Description Polish Release Notes](docs/release_notes_l13_4_product_description_polish.md) ? Product Description Mode ?????? release notes?
- [Product Description Polish Final Audit](docs/product_description_polish_final_audit.md) ? L13.4-G Product Description Mode ?????????
- [Public Demo Refresh L13.5 Product Description](docs/public_demo_refresh_l13_5_product_description.md) ? L13.5-A Product Description Demo v1 ???????
- [Public Demo Refresh Final Audit](docs/public_demo_refresh_final_audit.md) ? L13.5-B Public Demo refresh ?????
- [Product Description Polish v1 Archive](docs/product_description_polish_v1_archive.md) ? product-description-polish-v1 ?????
- [Language Mode Design](docs/language_mode_design.md) ? L13.6-A ?? / English ?????????
- [Language Mode API Contract](docs/language_mode_api_contract.md) ? L13.6-B Language Mode API contract ???
- [Language Mode Frontend Copy Map](docs/language_mode_frontend_copy_map.md) ? L13.6-C Language Mode ??????????
- [Language Mode Smoke Record](docs/language_mode_smoke_record.md) ? L13.6-F Language Mode smoke ???
- [Language Mode Final Audit](docs/language_mode_final_audit.md) ? L13.6-G Language Mode ?????
- [Public Demo Refresh L13.7 Language Mode](docs/public_demo_refresh_l13_7_language_mode.md) ? L13.7-A Language Mode ???????
- [Language Mode Public Refresh Final Audit](docs/language_mode_public_refresh_final_audit.md) ? L13.7-B Language Mode ?????????
- [Language Mode Heading Encoding Final Audit](docs/language_mode_heading_encoding_final_audit.md) ? L13.7-D Language Mode ???????????
- [Language Mode v1 Archive](docs/language_mode_v1_archive.md) ? language-mode-v1 ?????
- [Language Mode Trial Launch Checklist](docs/language_mode_trial_launch_checklist.md) ? L13.8-A Language Mode ???????????
- [Language Mode Trial Outreach Tracker](docs/language_mode_trial_outreach_tracker.md) ? L13.8-B Language Mode ????????????
- [Language Mode Trial Smoke Record](docs/language_mode_trial_smoke_record.md) ? L13.8-C Language Mode ??? smoke ???
- [Language Mode Trial Round 1 Summary Template](docs/language_mode_trial_round_1_summary_template.md) ? L13.8-D Language Mode ??????????
- [Language Mode Trial Launch Final Audit](docs/language_mode_trial_launch_final_audit.md) ? L13.8-E Language Mode ?????????
- [Trial Feedback Deferred Roadmap Decision](docs/trial_feedback_deferred_roadmap_decision.md) ? L13.9-A ??????????????
- [Pasted Reviews Input Design](docs/pasted_reviews_input_design.md) ? L14.0-A ?????????
- [Pasted Reviews API Contract Design](docs/pasted_reviews_api_contract_design.md) ? L14.0-B ?????? API contract ???
- [Pasted Reviews Frontend UX Design](docs/pasted_reviews_frontend_ux_design.md) ? L14.0-C ???????? UX ???
- [Pasted Reviews Implementation Plan](docs/pasted_reviews_implementation_plan.md) ? L14.0-D ???????????
- [Pasted Reviews Boundary Checklist](docs/pasted_reviews_boundary_checklist.md) ? L14.0-E ?????????????
- [Pasted Reviews Mode Smoke Record](docs/pasted_reviews_mode_smoke_record.md) ? L14.2-B ?????? smoke ???
- [L14 Pasted Reviews Mode Release Notes](docs/release_notes_l14_pasted_reviews_mode.md) ? L14 ?????? release notes?
- [Pasted Reviews Mode Final Audit](docs/pasted_reviews_mode_final_audit.md) ? L14.2-D ???????????
- [Public Demo Refresh L14.3 Pasted Reviews](docs/public_demo_refresh_l14_3_pasted_reviews.md) ? L14.3-A Pasted Reviews Mode ???????
- [Pasted Reviews Public Refresh Final Audit](docs/pasted_reviews_public_refresh_final_audit.md) ? L14.3-B Pasted Reviews Mode ?????????
- [Pasted Reviews Mode v1 Archive](docs/pasted_reviews_mode_v1_archive.md) ? pasted-reviews-mode-v1 ?????
- [Pasted Reviews Trial Launch Checklist](docs/pasted_reviews_trial_launch_checklist.md) ? L14.4-A Pasted Reviews ???????????
- [Pasted Reviews Trial Outreach Tracker](docs/pasted_reviews_trial_outreach_tracker.md) ? L14.4-B Pasted Reviews ????????
- [Pasted Reviews Trial Round 1 Summary Template](docs/pasted_reviews_trial_round_1_summary_template.md) ? L14.4-C Pasted Reviews ??????????
- [Pasted Reviews Trial Launch Final Audit](docs/pasted_reviews_trial_launch_final_audit.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Next Roadmap Decision](docs/pasted_reviews_next_roadmap_decision.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Input Guide Planning](docs/pasted_reviews_input_guide_planning.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Sample Review Library Planning](docs/pasted_reviews_sample_review_library_planning.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Polish Backlog](docs/pasted_reviews_polish_backlog.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Quality Rubric](docs/pasted_reviews_quality_rubric.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Public Demo Followup Checklist](docs/pasted_reviews_public_demo_followup_checklist.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews V1 Batch Final Audit](docs/pasted_reviews_v1_batch_final_audit.md) — Pasted Reviews 后续规划文档。
- [Pasted Reviews Input Guide Public Refresh](docs/pasted_reviews_input_guide_public_refresh.md) — L14.6-C 输入指南公网刷新记录。
- [Pasted Reviews Input Guide Final Audit](docs/pasted_reviews_input_guide_final_audit.md) — L14.6-D 输入指南最终审计。
- [L14.6 Pasted Reviews Input Guide Release Notes](docs/release_notes_l14_6_pasted_reviews_input_guide.md) — L14.6 输入指南 release notes。
- [Pasted Reviews Input Guide v1 Archive](docs/pasted_reviews_input_guide_v1_archive.md) — pasted-reviews-input-guide-v1 归档记录。
- [Pasted Reviews Next Polish Decision](docs/pasted_reviews_next_polish_decision.md) — L14.6-G 下一步 polish 决策。
- [Pasted Reviews Sample Library Public Refresh](docs/pasted_reviews_sample_library_public_refresh.md) — L14.7-C 示例评论库公网刷新记录。
- [Pasted Reviews Sample Library Final Audit](docs/pasted_reviews_sample_library_final_audit.md) — L14.7-D 示例评论库最终审计。
- [L14.7 Pasted Reviews Sample Library Release Notes](docs/release_notes_l14_7_pasted_reviews_sample_library.md) — L14.7 示例评论库 release notes。
- [Pasted Reviews Sample Library v1 Archive](docs/pasted_reviews_sample_library_v1_archive.md) — pasted-reviews-sample-library-v1 归档记录。
- [Pasted Reviews After Sample Library Decision](docs/pasted_reviews_after_sample_library_decision.md) — L14.7-G 示例评论库后续 polish 决策。
- [Pasted Reviews Review Count Public Refresh](docs/pasted_reviews_review_count_public_refresh.md) ? L14.8-C ?????????????
- [Pasted Reviews Review Count Final Audit](docs/pasted_reviews_review_count_final_audit.md) ? L14.8-D ???????????
- [L14.8 Pasted Reviews Review Count Release Notes](docs/release_notes_l14_8_pasted_reviews_review_count.md) ? L14.8 ?????? release notes?
- [Pasted Reviews Review Count v1 Archive](docs/pasted_reviews_review_count_v1_archive.md) ? pasted-reviews-review-count-v1 ?????
- [Pasted Reviews After Review Count Decision](docs/pasted_reviews_after_review_count_decision.md) ? L14.8-G ???????? polish ???
- [Pasted Reviews Pain Point Preview Public Refresh](docs/pasted_reviews_pain_point_preview_public_refresh.md) ? L14.9-C ???????????
- [Pasted Reviews Pain Point Preview Final Audit](docs/pasted_reviews_pain_point_preview_final_audit.md) ? L14.9-D ?????????
- [L14.9 Pasted Reviews Pain Point Preview Release Notes](docs/release_notes_l14_9_pasted_reviews_pain_point_preview.md) ? L14.9 ???? release notes?
- [Pasted Reviews Pain Point Preview v1 Archive](docs/pasted_reviews_pain_point_preview_v1_archive.md) ? pasted-reviews-pain-point-preview-v1 ?????
- [Pasted Reviews After Pain Point Preview Decision](docs/pasted_reviews_after_pain_point_preview_decision.md) ? L14.9-G ?????????
- [Pasted Reviews Polish Final Audit](docs/pasted_reviews_polish_final_audit.md) ? L14.10-A Pasted Reviews polish ?????
- [L14.10 Pasted Reviews Polish Release Notes](docs/release_notes_l14_10_pasted_reviews_polish.md) ? L14.10 Pasted Reviews polish release notes?
- [Pasted Reviews Polish v1 Archive](docs/pasted_reviews_polish_v1_archive.md) ? pasted-reviews-polish-v1 ?????
- [Pasted Reviews Input Experience Summary](docs/pasted_reviews_input_experience_summary.md) ? L14.10-D ???????
- [Pasted Reviews Post-Polish Roadmap Decision](docs/pasted_reviews_post_polish_roadmap_decision.md) ? L14.10-E ???????
- [L14 Final Handoff](docs/l14_pasted_reviews_final_handoff.md) ? L14 Pasted Reviews ???????
- [Public Demo Conversion Polish Planning](docs/public_demo_conversion_polish_planning.md) — L15.0-A 公网 demo 转化优化规划。
- [Public Demo Landing Hierarchy Design](docs/public_demo_landing_hierarchy_design.md) — L15.0-B Landing 层级设计。
- [Public Demo Primary CTA Waitlist Copy Plan](docs/public_demo_primary_cta_waitlist_copy_plan.md) — L15.0-C CTA / Waitlist 文案规划。
- [Public Demo Path Simplification Plan](docs/public_demo_path_simplification_plan.md) — L15.0-D 试用路径简化规划。
- [Public Demo Mobile Readability Checklist](docs/public_demo_mobile_readability_checklist.md) — L15.0-E 移动端可读性清单。
- [Public Demo Feedback Waitlist Tracking Plan](docs/public_demo_feedback_waitlist_tracking_plan.md) — L15.0-F Feedback / Waitlist 追踪计划。
- [Public Demo Conversion Polish Backlog](docs/public_demo_conversion_polish_backlog.md) — L15.0-G 转化优化 backlog。
- [Public Demo Conversion Polish Implementation Plan](docs/public_demo_conversion_polish_implementation_plan.md) — L15.0-H 实现计划。
- [Public Demo Hero CTA Public Refresh](docs/public_demo_hero_cta_public_refresh.md) ? L15.1-C Hero CTA ???????
- [Public Demo Hero CTA Final Audit](docs/public_demo_hero_cta_final_audit.md) ? L15.1-D Hero CTA ?????
- [L15.1 Public Demo Hero CTA Release Notes](docs/release_notes_l15_1_public_demo_hero_cta.md) ? L15.1 Hero CTA release notes?
- [Public Demo Hero CTA v1 Archive](docs/public_demo_hero_cta_v1_archive.md) ? public-demo-hero-cta-v1 ?????
- [Public Demo After Hero CTA Decision](docs/public_demo_after_hero_cta_decision.md) ? L15.1-G Hero CTA ?????
- [Public Demo Feedback Waitlist CTA Public Refresh](docs/public_demo_feedback_waitlist_cta_public_refresh.md) — L15.2-B Feedback / Waitlist CTA 公网刷新记录。
- [Public Demo Feedback Waitlist CTA Final Audit](docs/public_demo_feedback_waitlist_cta_final_audit.md) — L15.2-C Feedback / Waitlist CTA 最终审计。
- [Public Demo Mobile Readability Final Audit](docs/public_demo_mobile_readability_final_audit.md) — L15.3-B 移动端可读性最终审计。
- [Public Demo Result Follow-up CTA Public Refresh](docs/public_demo_result_followup_cta_public_refresh.md) — L15.4-B Result follow-up CTA 公网刷新记录。
- [Public Demo Result Follow-up CTA Final Audit](docs/public_demo_result_followup_cta_final_audit.md) — L15.4-C Result follow-up CTA 最终审计。
- [L15.2-15.4 Public Demo Conversion Release Notes](docs/release_notes_l15_2_3_4_public_demo_conversion.md) — L15.2 / L15.3 / L15.4 release notes。
- [L15.2-15.4 Public Demo Conversion Batch Final Audit](docs/public_demo_conversion_batch_final_audit_l15_2_3_4.md) — L15.2 / L15.3 / L15.4 批次最终审计。
- [Public Demo Conversion Polish v1 Archive](docs/public_demo_conversion_v1_archive.md) — public-demo-conversion-polish-v1 归档记录。
- [Public Demo Conversion Next Decision](docs/public_demo_conversion_next_decision.md) — L15.4-D 后续路线决策。
- [Trial Outreach Message Pack Planning](docs/trial_outreach_message_pack_planning.md) — L15.5-A 真实用户试用邀请文案规划。
- [Trial Outreach Message Pack v1](docs/trial_outreach_message_pack_v1.md) — L15.5-B 试用邀请文案包总览。
- [Trial Outreach CN Messages](docs/trial_outreach_cn_messages.md) — L15.5-C 中文试用邀请文案。
- [Trial Outreach EN Messages](docs/trial_outreach_en_messages.md) — L15.5-D 英文试用邀请文案。
- [Trial Outreach Follow-up Messages](docs/trial_outreach_followup_messages.md) — L15.5-E follow-up / feedback reminder 文案。
- [Trial Outreach Sending Checklist](docs/trial_outreach_sending_checklist.md) — L15.5-F 发送检查清单。
- [Trial Outreach Message Pack Final Audit](docs/trial_outreach_message_pack_final_audit.md) — L15.5-G 试用邀请文案包最终审计。
- [Trial Outreach Message Pack v1 Archive](docs/trial_outreach_message_pack_v1_archive.md) — trial-outreach-message-pack-v1 归档记录。
- [Trial Outreach First Round Execution Plan](docs/trial_outreach_first_round_execution_plan.md) — L15.5-I 第一轮真实试用执行计划。
- [Trial Outreach After Message Pack Decision](docs/trial_outreach_after_message_pack_decision.md) — L15.5-J 文案包后续决策。
- [Trial Feedback Round 1 Tracker](docs/trial_feedback_round_1_tracker.md) — L15.6-A 第一轮真实试用反馈 tracker。
- [Trial Feedback Signal Rubric](docs/trial_feedback_signal_rubric.md) — L15.6-B 反馈信号判断规则。
- [Trial Feedback Round 1 Summary Template](docs/trial_feedback_round_1_summary_template.md) — L15.6-C 第一轮反馈总结模板。
- [Trial Feedback Decision Matrix](docs/trial_feedback_decision_matrix.md) — L15.6-D 反馈后续路线矩阵。
- [Trial Feedback Tracker v1 Archive](docs/trial_feedback_tracker_v1_archive.md) — trial-feedback-tracker-v1 归档记录。
- [Result Readability Polish Planning](docs/result_readability_polish_planning.md) — L16.0-A 结果可读性优化规划。
- [Result Readability Section Map](docs/result_readability_section_map.md) — L16.0-B 结果区信息结构设计。
- [Result Readability Frontend Backlog](docs/result_readability_frontend_backlog.md) — L16.0-C 结果区前端 backlog。
- [Result Readability Boundary Checklist](docs/result_readability_boundary_checklist.md) — L16.0-D 结果可读性边界清单。
- [Result Readability Implementation Plan](docs/result_readability_implementation_plan.md) — L16.0-E 结果可读性实现计划。
- [L16.1-L16.3 Result Readability Public Refresh](docs/result_readability_public_refresh_l16_1_2_3.md) ? L16.1 / L16.2 / L16.3 ???????
- [Result Summary Hook Highlight Final Audit](docs/result_summary_hook_highlight_final_audit.md) ? L16.1 ?????
- [Storyboard Scene Readability Final Audit](docs/storyboard_scene_readability_final_audit.md) ? L16.2 ?????
- [Evidence Source Label Final Audit](docs/evidence_source_label_final_audit.md) ? L16.3 ?????
- [L16.1-L16.3 Result Readability Release Notes](docs/release_notes_l16_1_2_3_result_readability.md) ? L16.1 / L16.2 / L16.3 release notes?
- [Result Readability Polish v1 Archive](docs/result_readability_v1_archive.md) ? result-readability-polish-v1 ?????
- [Result Readability After v1 Decision](docs/result_readability_after_v1_decision.md) ? L16.3-D ?????
- [Result Readability Real Generation Smoke Record](docs/result_readability_real_generation_smoke_record.md) ? L16.4-A ???? smoke ???
- [Result Readability Real Generation Final Audit](docs/result_readability_real_generation_final_audit.md) ? L16.4-B ?????????
- [Result Readability Encoding Observation](docs/result_readability_encoding_observation.md) ? L16.4-C encoding / punctuation ?????
- [Result Readability Smoke v1 Archive](docs/result_readability_smoke_v1_archive.md) ? result-readability-smoke-v1 ?????
- [Result Readability After Smoke Decision](docs/result_readability_after_smoke_decision.md) ? L16.4-D smoke ?????
- [Trial Round 1 Execution Record](docs/trial_round_1_execution_record.md) ? L17.0-A ????????????
- [Trial Round 1 Send Log](docs/trial_round_1_send_log.md) ? L17.0-B ??????????
- [Trial Round 1 Feedback Inbox](docs/trial_round_1_feedback_inbox.md) ? L17.0-C ?????????
- [Trial Round 1 Daily Review Checklist](docs/trial_round_1_daily_review_checklist.md) ? L17.0-D ???????
- [Trial Round 1 Completion Criteria](docs/trial_round_1_completion_criteria.md) ? L17.0-E ????????
- [Trial Round 1 v1 Archive](docs/trial_round_1_v1_archive.md) ? trial-round-1-execution-v1 ?????
- [Trial Round 1 Simulated Feedback Record](docs/trial_round_1_simulated_feedback_record.md) ? L17.1-A ?????????
- [Chinese Onboarding Localization Decision](docs/chinese_onboarding_localization_decision.md) ? L17.1-B ?? onboarding ??????
- [Chinese Onboarding Flow Plan](docs/chinese_onboarding_flow_plan.md) ? L17.1-C ????????????
- [Dataset Language Gap Observation](docs/dataset_language_gap_observation.md) ? L17.1-D ??????????
- [Chat Guided Input Idea Note](docs/chat_guided_input_idea_note.md) ? L17.1-E ????????????
- [L17.1 Next Implementation Plan](docs/l17_1_next_implementation_plan.md) ? L17.1-F ????????
- [Chinese Onboarding Public Refresh L17.2-L17.4](docs/chinese_onboarding_public_refresh_l17_2_3_4.md) — L17.2 / L17.3 / L17.4 公网刷新记录。
- [Chinese Onboarding Final Audit](docs/chinese_onboarding_final_audit.md) — L17.2 中文 onboarding 最终审计。
- [Chinese Sample Product Library Final Audit](docs/chinese_sample_product_library_final_audit.md) — L17.3 示例产品库最终审计。
- [Chinese First-Run Guide Final Audit](docs/chinese_first_run_guide_final_audit.md) — L17.4 第一次试用引导最终审计。
- [L17 Chinese Onboarding Release Notes](docs/release_notes_l17_chinese_onboarding.md) — L17 中文 onboarding release notes。
- [Chinese Onboarding v1 Archive](docs/chinese_onboarding_v1_archive.md) — chinese-onboarding-polish-v1 归档记录。
- [Chinese Onboarding After v1 Decision](docs/chinese_onboarding_after_v1_decision.md) — L17.4-D 后续决策。
- [L18 Frontend UX Redesign Brief](docs/frontend_ux_redesign_brief_l18.md) ? L18.0-A ???????????
- [L18 Frontend UX User Journey Map](docs/frontend_ux_user_journey_l18.md) ? L18.0-B ???????
- [L18 Frontend UX New Layout Spec](docs/frontend_ux_new_layout_spec_l18.md) ? L18.0-C ????????
- [L18 Frontend UX Component Plan](docs/frontend_ux_component_plan_l18.md) ? L18.0-D ?????
- [L18 Frontend UX Result Placement Spec](docs/frontend_ux_result_placement_spec_l18.md) ? L18.0-E ?????????
- [L18 Codex Implementation Prompt](docs/frontend_ux_codex_prompt_l18.md) ? L18.0-F Codex ?????
- [L18 Frontend UX Boundary Checklist](docs/frontend_ux_boundary_checklist_l18.md) ? L18.0-G ?? UX ???????
- [L18 Public Demo Final Audit](docs/public_demo_l18_final_audit.md) — L18 final 中文试用版最终验收。
- [L18 Public Demo Release Notes](docs/public_demo_l18_release_notes.md) — L18 final 发布说明。
- [L18 Public Demo Archive](docs/public_demo_l18_archive.md) — L18 UX 重构归档。
- [L18 After Action Decision](docs/public_demo_l18_after_action_decision.md) — L18 后续决策。
- [L18 Friend Feedback Record](docs/public_demo_l18_friend_feedback_record.md) — L18 中文朋友反馈记录。
- [L18 Next Trial Plan](docs/public_demo_l18_next_trial_plan.md) — L18 下一轮中文试用计划。
- [L18 Public Demo Closure Summary](docs/public_demo_l18_closure_summary.md) — L18 收尾总结。
- [L18 Trial Feedback Template](docs/public_demo_l18_trial_feedback_template.md) — L18 试用反馈记录模板。
- [L18 Next Decision Gate](docs/public_demo_l18_next_decision_gate.md) — L18 后续是否继续改的决策门槛。
- [L18 Trial Round 2 Tracker](docs/public_demo_l18_trial_round_2_tracker.md) — L18 第二轮中文朋友试用记录表。
- [Amazon Product Link v1 Handoff](docs/amazon_product_link_v1_handoff.md) — L26-G Amazon Product Link primary path shipped and publicly verified.
