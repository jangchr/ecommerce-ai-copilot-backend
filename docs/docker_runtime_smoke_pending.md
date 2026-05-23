# Docker Runtime Smoke Pending Record

## Current Status

```text
L10.6-A Docker runtime smoke validation: BLOCKED
Reason: Docker CLI unavailable on current machine.
```

Docker runtime validation has not passed. The current machine cannot execute `docker build`, `docker run`, container `/healthz`, container preflight or container fast-gate checks because the Docker CLI is unavailable.

## Completed Static Packaging Boundary Check

The non-runtime packaging boundary has been inspected:

- `Dockerfile` copies application source, `data/reviews/` and `runs/baselines/` into the image layout.
- `data/reviews/`, `runs/baselines/l9_9_stable/` and `runs/baselines/l10_4_production_handoff/` exist in the local release workspace.
- `.dockerignore` excludes `.env`, virtual environments, cache files, mutable run output, runtime FAISS indexes, repository metadata and local server markers/logs.

This static review supports readiness for container testing, but it is not a substitute for an executed Docker runtime smoke test.

## Manual CI Execution Path

Because Docker is unavailable on the current machine, the smoke validation can be executed manually on a GitHub-hosted Docker runner through:

```text
.github/workflows/docker_smoke_manual.yml
```

Trigger **L10 Manual Docker Smoke** using GitHub Actions `workflow_dispatch`. The workflow builds the image, starts the smoke container with a non-production dummy API key, waits for `/healthz`, runs container startup preflight and the fast gate, checks required/excluded assets, and always removes the container.

The pending status remains in effect until a Docker-enabled execution of this workflow or the local command sequence below passes.

## Pending Runtime Validation

The following steps must be executed in a Docker-enabled environment before container promotion:

```powershell
docker build -t grounded-agent-backend .
docker run --rm --name grounded-agent-smoke -p 8001:8001 --env-file .env grounded-agent-backend
Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
docker exec grounded-agent-smoke python scripts/startup_preflight.py
docker exec grounded-agent-smoke python scripts/run_all_tests.py --fast
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert Path('/app/data/reviews').is_dir(); assert Path('/app/runs/baselines/l9_9_stable').is_dir(); assert Path('/app/runs/baselines/l10_4_production_handoff').is_dir(); print('required assets present')"
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert not Path('/app/.env').exists(); assert not Path('/app/runs/latest').exists(); assert not Path('/app/runs/history').exists(); assert not Path('/app/storage/faiss_memory').exists(); print('excluded assets absent')"
```

## Passing Criteria

L10.6-A can be marked complete only when:

- Image build succeeds.
- The container starts and serves `GET /healthz`.
- Container `startup_preflight.py` passes.
- Container fast gate passes.
- Required grounded datasets and both approved baseline artifacts are present inside the image.
- Runtime secrets, mutable regression output and prebuilt FAISS runtime indexes are absent inside the image.

## Related Documents

- [Docker Smoke Protocol](docker_smoke_protocol.md): canonical container validation procedure.
- [Production Handoff Runbook](production_handoff_runbook.md): operating and handoff expectations.
- [Release Artifact Manifest](release_artifact_manifest.md): package content and persistence boundary.
- [L10.4 Production Handoff Release Notes](release_notes_l10_4_production_handoff.md): latest handoff baseline status.

