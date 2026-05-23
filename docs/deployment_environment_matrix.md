# Deployment Environment Matrix

## Purpose

This matrix defines deployment and validation expectations for the grounded ecommerce creative agent backend. The stable reference point is:

```text
runs/baselines/l9_9_stable/
```

The local curated review dataset remains the regression anchor in every environment. External real-source adapters are not part of the default product runtime.

## Common Safety Defaults

| Setting / Boundary | Default Policy |
| --- | --- |
| `ALLOW_REAL_SOURCE_ADAPTERS` | `false` |
| `MEMORY_MAX_RECORD_COUNT` | `500` |
| Product API | `/api/v1/generate-copilot` never exposes debug telemetry or internal state. |
| Debug trace API | `/api/v1/debug-copilot` is diagnostic-only and should be access-controlled outside local development. |
| Debug source probe | `/api/v1/debug-source-probe` only inspects real-source shells, never writes memory and never executes local/mock regression anchors. |
| Regression anchor | `data/reviews/*.json` must remain available for baseline testing. |
| Health check | `GET /healthz` returns lightweight service metadata and must not trigger workflow, LLM or source adapter calls. |

## Environment Summary

| Environment | Python Version | `OPENAI_API_KEY` | `OPENAI_API_BASE` / `MODEL_NAME` | `ALLOW_REAL_SOURCE_ADAPTERS` | `MEMORY_MAX_RECORD_COUNT` | Debug Source Probe |
| --- | --- | --- | --- | --- | --- | --- |
| Local development | Python 3.12 verified; pin local venv | Required only for live product/full-regression requests | Local `.env`; default compatible endpoint and `deepseek-chat` unless intentionally changed | `false` | `500` | Allowed for developer diagnostics; disabled real shells only |
| CI fast gate | Pin Python 3.12 | Not required | Not required for mocked/fast checks | `false` | `500` | Contract and smoke tests only; no network execution |
| CI/manual full regression | Pin Python 3.12 | Required | Explicit secret/configuration for the accepted LLM endpoint and model | `false` | `500` | Not required for quality run; may be tested independently without enabling real sources |
| Staging | Pin one production-candidate version: Python 3.11 or 3.12 | Required for workflow requests | Staging secret/config, matching intended model policy | `false` by default | `500` unless a reviewed capacity change is approved | Allowed only behind debug/admin access; must remain memory-write disabled |
| Production | Pin one deployed version: Python 3.11 or 3.12 | Required for product workflow | Deployment secret/config, explicitly versioned and monitored | `false` | `500` until a release-reviewed change | Disabled or tightly access-controlled; never part of product request flow |

## Storage, Cache And Artifact Policy

| Environment | FAISS / Sentence-Transformers Cache | `storage/memory_records.json` | `runs/latest/` | `runs/history/` | `runs/baselines/` |
| --- | --- | --- | --- | --- | --- |
| Local development | FAISS preferred; local embedding cache may persist. Observable `json_fallback` is acceptable with `faiss_error`. | Persist locally for development; do not treat ad hoc memory as a committed baseline fixture. | Local latest full run; disposable. | Optional local investigation archive; disposable unless intentionally retained. | Keep manually frozen milestone assets. |
| CI fast gate | Cache optional; tests must not rely on live vector downloads or mutable memory state. | Ephemeral test/runtime output only. | Not required. | Not retained. | Checkout read-only baselines required by tests. |
| CI/manual full regression | Cache embeddings/dependencies when available to reduce run variance; record backend/fallback telemetry. | Use isolated workspace storage for the run; retain only when required for investigation. | Publish as run artifact for the latest executed suite. | Archive accepted/investigated run artifacts according to CI retention. | Read stable baseline for comparison; new baseline freezing remains deliberate. |
| Staging | Provision persistent FAISS/cache storage where practical; monitor fallback state. | Persist across staging restarts only when memory evaluation is intended; support reset/reseed procedure. | Retain the latest validation run. | Retain time-bounded validation history for diagnosis. | Mount or ship accepted baselines as immutable artifacts. |
| Production | Persistent FAISS/cache volume expected; alert on `json_fallback` or non-zero fallback counts. | Persist on managed durable storage with backup/retention policy; never rely on container ephemeral disk. | Production does not generate regression reports by normal product traffic. | Store only scheduled validation artifacts under approved retention policy. | Deploy frozen baselines as immutable release/reference artifacts. |

## Environment Details

### Local Development

- Use the verified Python 3.12 virtual environment documented in the [README](../README.md).
- Keep `ALLOW_REAL_SOURCE_ADAPTERS=false`; local reviews plus mock trend signals remain the normal execution inputs.
- `OPENAI_API_KEY` is needed for live workflow execution and full regression, but not for fast unit/smoke validation.
- Developers may use `/api/v1/debug-source-probe` to inspect disabled real-source shells. It remains a no-network, no-memory-write surface at the current implementation stage.

### CI Fast Gate

- Execute `scripts/run_all_tests.py --fast` with Python 3.12.
- Do not require LLM secrets or mutable runtime memory.
- The API and source-probe smoke tests prove endpoint boundaries through patched workflow execution and disabled adapter shells.
- No report history or memory state from fast CI should be promoted as a baseline.

### CI Or Manual Full Regression

- Execute `scripts/run_all_tests.py` with configured LLM credentials.
- Always retain `regression_summary.csv`, `telemetry_node_aggregate.csv`, `cost_gate_summary.csv` and `regression_report.md` for release decisions.
- Compare quality against frozen baselines while keeping absolute grounded gates as hard requirements.
- Do not enable real-source adapters for baseline regression; local datasets keep the result attributable and reproducible.

### Staging

- Mirror production environment variables and persistent storage layout as closely as possible.
- Run `/healthz` at deployment startup and before workflow validation.
- Keep product traffic on local/mock-safe source defaults until an explicit real-source promotion decision exists.
- Permit debug endpoints only behind internal authorization and log their use separately from product calls.

### Production

- `ALLOW_REAL_SOURCE_ADAPTERS=false` is the required default release posture.
- `/api/v1/generate-copilot` must remain product-only and must not reveal telemetry, cognitive state, memory state or debug traces.
- Return `X-Request-ID` on every response and preserve caller-provided IDs when present for end-to-end correlation.
- Emit structured JSON API logs correlated by `request_id`; log only endpoint/status/latency and approved summary fields, never secrets, complete prompts or raw evidence content.
- Restrict body-level `request_id`, `telemetry_summary` and `memory_observability` to authorized debug surfaces; keep them out of product response bodies.
- Preserve local dataset files and frozen regression baselines in the release package or its validation artifact bundle.
- `/healthz` is suitable for platform liveness/readiness polling because it never invokes the workflow.
- Any future activation of real adapters requires a separately reviewed rollout, failure fallback validation and non-pollution proof for success memory.

## Docker Packaging

The supported container entry point is the repository `Dockerfile`, based on Python 3.12 slim and launched with:

```text
uvicorn main:app --host 0.0.0.0 --port 8001
```

Container policy:

- Inject `OPENAI_API_KEY`, `OPENAI_API_BASE` and `MODEL_NAME` at runtime; never bake `.env` into the image.
- Keep `ALLOW_REAL_SOURCE_ADAPTERS=false` unless a separately approved source rollout is being validated.
- Include `data/reviews/` and `runs/baselines/` in the image or mounted release artifact set. Frozen baselines are release assets and must remain available for regression and diagnostic comparison.
- Exclude `runs/latest/`, `runs/history/` and `storage/faiss_memory/` from the image context. These are mutable runtime or validation outputs.
- In staging or production, mount durable storage for `storage/memory_records.json` and FAISS/cache state when persistent memory is required.
- Configure container orchestration health checks against `GET /healthz`; it is intentionally independent of LLM and source-provider availability.
- Validate build contents, secret exclusion and optional in-container fast checks with the [Docker Smoke Protocol](docker_smoke_protocol.md).

## Startup Preflight

Run `python scripts/startup_preflight.py` before launching a packaged deployment or as an image-validation step. It emits JSON and fails only for startup-blocking package conditions:

- Missing `data/reviews/` or fewer than ten local review datasets.
- Missing `runs/baselines/l9_9_stable/`.
- Missing `requirements.txt` or `.env.example`.
- Invalid non-positive `MEMORY_MAX_RECORD_COUNT`.

The startup preflight reports whether `OPENAI_API_KEY` is present without treating absence as a blocker, and it may report whether `faiss` can be imported without initializing embeddings or downloading models. It does not invoke the workflow, an LLM or an external API.

## Preflight Reference

| Check | Command / Endpoint |
| --- | --- |
| Packaged startup assets and safe defaults | `python scripts/startup_preflight.py` |
| Environment, datasets and baseline presence | `.\l8\Scripts\python.exe scripts\check_env.py` |
| FAISS backend health | `.\l8\Scripts\python.exe scripts\check_faiss_backend.py` |
| API liveness/readiness | `GET /healthz` |
| Fast boundary regression | `.\l8\Scripts\python.exe scripts\run_all_tests.py --fast` |
| Full grounded regression | `.\l8\Scripts\python.exe scripts\run_all_tests.py` |

## Related Documents

- [README](../README.md): setup, commands and API entry points.
- [Architecture Map](architecture_map.md): runtime layers and guarded data flow.
- [Regression Protocol](regression_protocol.md): gates, telemetry and baseline policy.
- [Release Checklist](release_checklist.md): release-time execution and blocker review.
- [Frontend Smoke Protocol](frontend_smoke_protocol.md): debug UI and endpoint separation checks.
