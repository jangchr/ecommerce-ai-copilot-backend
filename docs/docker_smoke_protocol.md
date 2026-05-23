# Docker Smoke Protocol

## Purpose

This protocol validates the Docker packaging boundary for the grounded ecommerce creative agent backend. It is intended for a workstation or CI runner with Docker installed; it is not required to run on machines without Docker.

The protocol checks:

- The service image builds and starts with runtime-injected environment variables.
- `GET /healthz` responds without invoking the workflow.
- Grounded review anchors and frozen baseline assets are present.
- Secrets, mutable run output and runtime vector indexes are not packaged into the image.

## Prerequisites

1. Start from the `backend` directory.
2. Ensure Docker is installed and the Docker daemon is running.
3. Prepare a local `.env` for container execution. It is passed at runtime and must never be copied into the image.

## 1. Build The Image

```powershell
docker build -t grounded-agent-backend .
```

Expected:

- The build uses `python:3.12-slim`.
- Dependencies install from `requirements.txt`.
- The image includes application source, local grounded review datasets and frozen baselines.
- `.dockerignore` prevents local secrets and mutable runtime output from entering the build context.

## 2. Run The Container

```powershell
docker run --rm -p 8001:8001 --env-file .env grounded-agent-backend
```

Expected:

- The container starts `uvicorn main:app --host 0.0.0.0 --port 8001`.
- `OPENAI_API_KEY` and model settings enter the process only through runtime environment injection or a deployment secret manager.
- The default runtime safety posture remains `ALLOW_REAL_SOURCE_ADAPTERS=false`.

For commands that inspect a running container, start it with a name in a second run:

```powershell
docker run --rm --name grounded-agent-smoke -p 8001:8001 --env-file .env grounded-agent-backend
```

## 3. Verify Health

With the container running:

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

`/healthz` is intentionally independent of workflow execution, LLM availability and source adapter availability.

## 4. Optional Container Startup Preflight

Run the lightweight packaged-service preflight inside the named running container:

```powershell
docker exec grounded-agent-smoke python scripts/startup_preflight.py
```

Expected:

- JSON output with `status: "pass"`, an empty `required_failures` list and detailed `checks`.
- The check confirms local review data, frozen stable baseline and memory-capacity configuration.
- A missing `OPENAI_API_KEY` is reported but is not a startup-preflight hard failure.
- The script does not run workflow or LLM calls and does not reach external source APIs.

## 5. Verify Packaged And Excluded Assets

Run these inspections against the named running container:

```powershell
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert Path('/app/data/reviews').is_dir(); assert Path('/app/runs/baselines/l9_9_stable').is_dir(); print('required assets present')"
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert not Path('/app/.env').exists(); assert not Path('/app/runs/latest').exists(); assert not Path('/app/runs/history').exists(); assert not Path('/app/storage/faiss_memory').exists(); print('excluded assets absent')"
```

Required inside the image:

- `data/reviews/`
- `runs/baselines/`, including `runs/baselines/l9_9_stable/`

Must not be copied into the image:

- `.env`
- `runs/latest/`
- `runs/history/`
- `storage/faiss_memory/`

The image may create mutable runtime state only after it starts; persistent production memory must be mounted on managed durable storage rather than baked into an image.

## 6. Optional Container Fast Gate

Because `tests/` and `scripts/` are packaged, the fast boundary suite can be executed inside the image:

```powershell
docker exec grounded-agent-smoke python scripts/run_all_tests.py --fast
```

Expected:

- Compilation, unit, API smoke, failure and routing checks pass.
- The fast gate does not require a live LLM key and does not make real source-provider calls.

## 7. Shutdown

If the container was started in the foreground, stop it with `Ctrl+C`. If started detached or from another shell:

```powershell
docker stop grounded-agent-smoke
```

## GitHub Actions Manual Execution

When Docker is unavailable on a local workstation, run the same boundary validation on a GitHub-hosted runner using:

```text
.github/workflows/docker_smoke_manual.yml
```

Trigger the **L10 Manual Docker Smoke** workflow manually with `workflow_dispatch`. It performs:

- `docker build -t grounded-agent-backend .`
- Container startup using `OPENAI_API_KEY=dummy-for-smoke` and `ALLOW_REAL_SOURCE_ADAPTERS=false`.
- Retry-based `GET /healthz` validation.
- Container `python scripts/startup_preflight.py`.
- Container `python scripts/run_all_tests.py --fast`.
- Required asset checks for `data/reviews/`, `runs/baselines/l9_9_stable/` and `runs/baselines/l10_4_production_handoff/`.
- Exclusion checks for `.env`, `runs/latest/`, `runs/history/` and `storage/faiss_memory/`.
- Container removal under `always()`, including failed runs.

This workflow does not make real source-provider calls and does not constitute a full LLM regression run.

## Passing Criteria

A Docker smoke run passes when:

- `docker build` succeeds.
- The container starts on port `8001`.
- `/healthz` returns the expected service and baseline identity.
- Required dataset and baseline assets are available inside the image.
- `.env`, latest/history run artifacts and prebuilt runtime FAISS indexes are absent.
- Optional in-container fast gate passes when executed.

## Related Documents

- [README](../README.md): setup and container quick-start commands.
- [Deployment Environment Matrix](deployment_environment_matrix.md): environment-specific persistence and access policy.
- [Release Checklist](release_checklist.md): release sign-off sequence.
- [Architecture Map](architecture_map.md): endpoint and runtime boundaries.
- [Docker Runtime Smoke Pending Record](docker_runtime_smoke_pending.md): pending status and the manual CI execution path.
