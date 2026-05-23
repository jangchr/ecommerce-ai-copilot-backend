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

## Safety Posture

| Boundary | Operating Rule |
| --- | --- |
| Default source policy | Keep `ALLOW_REAL_SOURCE_ADAPTERS=false`; local review datasets and mock trend signals remain the regression anchors. |
| Product output | `/api/v1/generate-copilot` returns product content only; it must not expose `request_id`, `telemetry_summary`, memory state or other debug internals in the response body. |
| Debug output | `/api/v1/debug-copilot` and `/api/v1/debug-source-probe` are diagnostic surfaces and should be access-controlled outside local development. |
| Health polling | `/healthz` is safe for liveness/readiness polling because it does not invoke workflow, LLM calls or source adapters. |
| Correlation and logs | Every response returns `X-Request-ID`; structured logs use the request ID and safe summary fields only. |
| Memory | Only grounded, approved outcomes qualify for success memory; memory capacity remains bounded. |

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
- [Release Artifact Manifest](release_artifact_manifest.md): package contents, exclusions and durable-runtime state policy.
- [L10.4 Production Handoff Release Notes](release_notes_l10_4_production_handoff.md): latest validated handoff baseline, costs, memory status and Docker smoke boundary.
