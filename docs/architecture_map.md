# Architecture Map

## System Purpose

This backend is a grounded ecommerce creative agent runtime: evidence enters through controlled source adapters, moves through structured cognition and creative generation, is evaluated for both quality and grounding, and is stored only under observable memory rules.

## Data Flow

```text
Product request
    |
    v
API Layer
  GET /healthz                     lightweight service readiness only
  /api/v1/generate-copilot       /api/v1/debug-copilot
  product-facing output          evidence + state + telemetry + memory health
                                  /api/v1/debug-source-probe
                                  real-source shell status only; no memory writes
    |                              |
    +--------------+---------------+
                   v
Workflow Runtime (LangGraph)
  Planner -> Retrieval -> Evidence Builder -> Parallel Analysis
                                                |
                                                v
  Analytics Memory <- Governance <- Storyboard <- Strategy <- Cognitive Synthesis
                         |
                         v
                     Reflection
                       |   |
               regenerate  patch then re-evaluate
    ^
    |
Source Adapter Layer
  local_review_dataset + tiktok_trend_mock          default enabled anchors
  amazon/tiktok/reddit real adapters                disabled unavailable shells

Grounding & Reward
  evidence quotes -> scene quote binding -> creative_score / grounded_score
  -> grounded_ctr / failure_type -> regeneration route or accepted memory write

Memory & Regression
  bounded JSON records <-> FAISS backend (JSON fallback observable)
  fast/full gates -> reports -> manually frozen baselines
```

## API Layer

`main.py` exposes a lightweight health check and three response-model-protected application endpoints:

| Endpoint | Boundary |
| --- | --- |
| `GET /healthz` | Deployment health metadata only: static service status and stable baseline identity. It does not run the workflow, call an LLM or fetch any source adapter. |
| `POST /api/v1/generate-copilot` | Product response only: insights, audience, strategy, assets, evaluation and feedback. It must not expose `data.debug` or internal graph state. |
| `POST /api/v1/debug-copilot` | Diagnostic response: evidence, cognitive/execution state, world metrics, raw telemetry plus safe aggregate `telemetry_summary`, memory observability, revision count and regeneration target. |
| `POST /api/v1/debug-source-probe` | Debug-only status probe for real-source adapter shells. It does not execute the product workflow or allow memory writes. |

The frontend uses the product endpoint for its main presentation. With Debug Mode enabled it makes an additional debug request; a debug failure is isolated from already-rendered product output.

Every HTTP response includes `X-Request-ID`: the API preserves an incoming value when provided and otherwise generates a UUID. The two debug response bodies also mirror `request_id` for diagnosis, while the product response body intentionally does not. API-layer structured logs use that identifier for correlation and contain only endpoint/status/timing and permitted summary fields, never complete evidence text, prompts or secrets.

The Debug API also exposes `telemetry_summary` as a bounded per-request view containing only node counts, aggregate token/latency totals, failed-node names and hotspot node names. The Product API does not expose this diagnostic summary.

## Production Observability

| Signal | Exposure Boundary |
| --- | --- |
| `X-Request-ID` | Returned on every HTTP response for cross-service/request correlation. |
| `request_id` in body | Returned only by the debug response surfaces for operator diagnosis. |
| Structured JSON logs | API-layer events correlate by request ID and include endpoint, status, latency and permitted summary dimensions only. |
| `telemetry_summary` | Debug-only bounded aggregate for per-request node count, token/latency totals, failed nodes and hotspot nodes. |
| Product/debug separation | Product response body remains free of `request_id`, telemetry summary and internal observability state. |

## Workflow Runtime

The graph in `core/workflow.py` processes a request through these stages:

| Stage | Responsibility |
| --- | --- |
| `planner` | Determine category, complexity and allowed source-tool plan. |
| `retrieval` | Execute selected source adapters and capture source/fallback trace. |
| `evidence_builder` | Aggregate review evidence and trend signals with confidence metadata. |
| `parallel_analysis` | Extract audience, painpoint and dopamine views from evidence. |
| `cognitive_synthesis` | Compile analysis into a structured cognitive profile. |
| `strategy` | Decide evidence-based creative positioning and conversion logic. |
| `storyboard` | Produce an executable, quote-linked scene graph. |
| `governance` | Calculate reward/grounding metrics and decide whether repair is required. |
| `reflection` | Patch or regenerate the layer indicated by the failure route. |
| `analytics` | Record final success/failure memory and telemetry. |

Dependency-aware routing prevents strategy or storyboard generation before required evidence and cognitive state exist. Governance accepts a result only when both creative and grounding criteria pass, or when revision limits terminate the run for recording.

## Source Adapter Layer

`source_adapters/` isolates data sources behind a shared contract and registry:

| Source | Current Role | Runtime Status |
| --- | --- | --- |
| `local_review_dataset` | Grounded review evidence from `data/reviews/*.json` | Enabled by default |
| `tiktok_trend_mock` | Stable trend-expression signal for regression | Enabled by default |
| `amazon_review_api` | Future real review source | Disabled unavailable shell |
| `tiktok_trend_api` | Future real trend source | Disabled unavailable shell |
| `reddit_review_api` | Future real review/community source | Disabled unavailable shell |

`ALLOW_REAL_SOURCE_ADAPTERS=false` is the safe default. Even if real-source tool names are exposed behind the flag, the current shells make no network requests and return `unavailable`, allowing retrieval to fall back to local/mock anchors.

`/api/v1/debug-source-probe` is a separate inspection boundary: by default it addresses only the Amazon, TikTok and Reddit real-source shells. It rejects local/mock anchor execution through the probe surface and always returns `memory_write_allowed=false`.

## Grounding And Reward

Evidence is kept distinct by purpose: review quotes support painpoint grounding, while trend signals inform expression. Storyboard scenes bind their `linked_painpoint` and `evidence_quote_used` to retrieved evidence.

The reward layer observes:

- Creative quality signals such as visual/narration sufficiency and retention design.
- Evidence alignment between scenes and review evidence.
- Source confidence and grounded quality, including `grounded_ctr`.
- Failure types including low source confidence, missing evidence alignment, weak visuals and reward hacking.

Failure types feed deterministic regeneration targets: evidence weakness can return to retrieval, while storyboard-expression failures return to storyboard/reflection handling.

## Memory Layer

The memory runtime stores outcome records under bounded and observable rules:

| Capability | Behavior |
| --- | --- |
| Success/failure separation | Only grounded approved outcomes qualify as success memory. |
| Capacity control | `MEMORY_MAX_RECORD_COUNT` defaults to `500`; retained capacity and pruning are observable. |
| Semantic retrieval | FAISS is the preferred vector backend when dependencies and embeddings are available. |
| Degraded operation | JSON fallback is allowed in constrained environments and must expose `faiss_error` and fallback trace. |
| Observability | Backend, record count, remaining capacity, pruned count, fallback count and traces appear in debug/telemetry surfaces. |

## Regression Layer

Regression protects quality, behavior and operating cost:

| Layer | Command / Artifact | Purpose |
| --- | --- | --- |
| Fast gate | `scripts/run_all_tests.py --fast` | Compilation, unit, API smoke, failure and routing checks without live LLM regression. |
| Full gate | `scripts/run_all_tests.py` | Ten-category grounded live regression and report generation. |
| Reports | `runs/latest/`, `runs/history/<timestamp>/` | Quality, telemetry and cost summaries for each accepted or investigated run. |
| Baselines | `runs/baselines/` | Manually frozen milestone comparisons; current stable baseline is `l9_9_stable`, with `l9_6_f_faiss_recovery` retained as a historical milestone. |
| Cost gate | `runs/latest/cost_gate_summary.csv` | Enforce token/node failure ceilings and expose latency warning bands. |

Absolute grounded gates remain hard requirements. Relative `grounded_ctr` drift may be recorded as a warning when the absolute gate still passes, making live model variance visible without hiding true regressions.

## Related Documents

- [README](../README.md): setup, execution and stable baseline entry point.
- [Regression Protocol](regression_protocol.md): thresholds, telemetry and baseline rules.
- [Frontend Smoke Protocol](frontend_smoke_protocol.md): manual frontend/API boundary checks.
- [API Examples](api_examples.md): product/debug API cookbook.
- [Release Checklist](release_checklist.md): release sign-off sequence and blockers.
