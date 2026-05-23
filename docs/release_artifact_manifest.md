# Release Artifact Manifest

## Purpose

This manifest defines the contents and exclusions for the grounded ecommerce creative agent backend source distribution, container image and release handoff package.

Current stable release artifact:

```text
runs/baselines/l9_9_stable/
```

The `data/reviews/` directory is the local grounded regression anchor and must not be removed from a release that is expected to support validation or diagnostics. Environment secrets must always be injected at runtime; `.env` must never be included in a source archive or image.

## A. Required In Source, Image Or Release Package

These assets form the executable service, its validation boundary and its stable comparison reference:

| Asset | Purpose |
| --- | --- |
| `main.py` | FastAPI application entry point and protected API surface. |
| `core/` | Workflow runtime support, telemetry and logging utilities. |
| `schemas/` | API and source-probe contracts. |
| `source_adapters/` | Local/mock anchors, registry and disabled real-source shells. |
| `scripts/` | Preflight, FAISS diagnostics, regression execution and baseline tools. |
| `tests/` | Fast gate safety, API and boundary verification. |
| `data/reviews/` | Ten-category grounded local regression anchor. |
| `docs/` | Operation, deployment, API and release documentation. |
| `static/` | Product/debug frontend surface. |
| `requirements.txt` | Runtime dependency input. |
| `requirements.lock.txt` | Verified environment snapshot. |
| `.env.example` | Non-secret configuration template. |
| `Dockerfile` | Production packaging definition. |
| `.dockerignore` | Container build-context safety boundary. |
| `runs/baselines/l9_9_stable/` | Current stable baseline and release comparison artifact. |

For a container image, package the required application assets and frozen baseline exactly as defined by `Dockerfile`. For a source release or handoff bundle, retain this same functional content so startup preflight and regression comparison remain possible.

## B. Required Exclusions

These items must not enter a committed release package or container image:

| Excluded Asset | Reason |
| --- | --- |
| `.env` and `.env.local` | Contains runtime secrets or environment-specific configuration. |
| `l8/`, `.venv/`, `venv/` | Local interpreter environments are not portable release assets. |
| `__pycache__/`, `*.pyc` | Generated interpreter cache. |
| `runs/latest/` | Mutable latest-run output, not a frozen release reference. |
| `runs/history/` | Mutable/historical diagnostic output, managed separately from a package. |
| Top-level `runs/*.json` | Per-run working output, not release content. |
| `storage/faiss_memory/` | Mutable runtime index; it must not be baked into an image. |
| `.git/` | Source-control metadata, not runtime content. |
| `.server.pid`, `.server.job`, `server.err.log`, `server.out.log`, `server.job.log` | Local process markers and logs. |

The exclusions are reinforced by `.dockerignore` and `.gitignore`. Before shipping a container, use the [Docker Smoke Protocol](docker_smoke_protocol.md) to verify both required and excluded contents.

## C. Runtime-Persistent State

These assets are not static release content but may need durable storage in a deployed environment:

| Runtime State | Persistence Policy |
| --- | --- |
| `storage/memory_records.json` | Persist on managed durable storage when accumulated memory must survive process or container replacement. Apply backup and capacity policy. |
| FAISS index and sentence-transformers cache state | Persist or mount when production uses long-lived semantic memory; monitor backend/fallback health and never ship mutable indexes as baseline code artifacts. |
| Production structured logs | Collect through the platform logging system using `X-Request-ID` / `request_id` correlation. Do not write operational logs into the release package. |

The default memory capacity remains controlled by:

```dotenv
MEMORY_MAX_RECORD_COUNT=500
```

## D. Regenerable Or Disposable Output

These items may be discarded and regenerated as needed:

| Asset | Regeneration Path |
| --- | --- |
| `runs/latest/` | Recreated by the next full regression run. |
| `runs/history/` | Recreated for future runs; retain separately only when required for audit or investigation. |
| `__pycache__/` and `*.pyc` | Recreated automatically by Python. |
| Runtime FAISS indexes | Rebuilt from approved retained memory/backend initialization when necessary; preserve durable production state separately when required. |
| Local debug/server logs | Recreated during local diagnostics; not release artifacts. |

## Product And Debug Artifact Boundary

- The Product API (`/api/v1/generate-copilot`) relies on executable runtime code and approved runtime state; it does not depend on debug report artifacts.
- Product responses must not expose `request_id`, `telemetry_summary`, memory observability or internal debug state in their body.
- Debug reports, run history and probe results are diagnostic assets only; they must not become implicit product-runtime dependencies.
- Frozen `runs/baselines/l9_9_stable/` is included for release validation and diagnostics, not to add debug fields to product output.

## Packaging Verification Checklist

- [ ] Required files and directories in section A are present.
- [ ] `data/reviews/` contains the grounded regression anchor datasets.
- [ ] `runs/baselines/l9_9_stable/` is included as the current stable release artifact.
- [ ] `.env` is absent and secrets are injected only at runtime.
- [ ] Mutable run output, FAISS runtime indexes and local logs are absent.
- [ ] Persistent memory/cache/log paths are provisioned by the target platform as required.
- [ ] Startup preflight and fast gate have passed for the packaged artifact.

## Related Documents

- [README](../README.md): setup and quick operational entry point.
- [Production Handoff Runbook](production_handoff_runbook.md): startup, validation and incident response.
- [Deployment Environment Matrix](deployment_environment_matrix.md): persistence and exposure policy by environment.
- [Docker Smoke Protocol](docker_smoke_protocol.md): image-content and container verification.
- [Release Checklist](release_checklist.md): release approval process.
