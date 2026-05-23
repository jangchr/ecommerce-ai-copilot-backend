# Docker Runtime Smoke Validation Record

## Current Status

```text
L10.6-A Docker runtime smoke validation: PASSED
Execution environment: GitHub Actions - L10 Manual Docker Smoke
```

Docker runtime smoke validation passed on a Docker-enabled GitHub Actions runner through `.github/workflows/docker_smoke_manual.yml`.

The current local machine still cannot execute `docker build`, `docker run`, container `/healthz`, container preflight or container fast-gate checks because the Docker CLI is unavailable. This local limitation no longer blocks container validation because the CI Docker runtime path has completed successfully.

## Completed Static Packaging Boundary Check

The non-runtime packaging boundary has been inspected:

- `Dockerfile` copies application source, `data/reviews/` and `runs/baselines/` into the image layout.
- `data/reviews/`, `runs/baselines/l9_9_stable/` and `runs/baselines/l10_4_production_handoff/` exist in the local release workspace.
- `.dockerignore` excludes `.env`, virtual environments, cache files, mutable run output, runtime FAISS indexes, repository metadata and local server markers/logs.

This static review was supplemented by the completed GitHub Actions runtime smoke execution.

## Validated CI Execution Path

Because Docker is unavailable on the current machine, the smoke validation can be executed manually on a GitHub-hosted Docker runner through:

```text
.github/workflows/docker_smoke_manual.yml
```

The **L10 Manual Docker Smoke** GitHub Actions workflow was triggered with `workflow_dispatch` and passed. It built the image, started the smoke container with a non-production dummy API key, waited for `/healthz`, ran container startup preflight and the fast gate, checked required/excluded assets, and removed the container.

Use the same workflow for repeatable future container-release validation when a local Docker runtime is unavailable.

## Revalidation Commands

The validated runtime path is reproduced by the following commands on any Docker-enabled environment:

```powershell
docker build -t grounded-agent-backend .
docker run --rm --name grounded-agent-smoke -p 8001:8001 --env-file .env grounded-agent-backend
Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
docker exec grounded-agent-smoke python scripts/startup_preflight.py
docker exec grounded-agent-smoke python scripts/run_all_tests.py --fast
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert Path('/app/data/reviews').is_dir(); assert Path('/app/runs/baselines/l9_9_stable').is_dir(); assert Path('/app/runs/baselines/l10_4_production_handoff').is_dir(); print('required assets present')"
docker exec grounded-agent-smoke python -c "from pathlib import Path; assert not Path('/app/.env').exists(); assert not Path('/app/runs/latest').exists(); assert not Path('/app/runs/history').exists(); assert not Path('/app/storage/faiss_memory').exists(); print('excluded assets absent')"
```

## Passing Criteria Satisfied

L10.6-A is complete because the CI Docker smoke run verified:

- Image build succeeded.
- The container started and served `GET /healthz`.
- Container `startup_preflight.py` passed.
- Container fast gate passed.
- Required grounded datasets and both approved baseline artifacts were present inside the image.
- Runtime secrets, mutable regression output and prebuilt FAISS runtime indexes were absent inside the image.

## Related Documents

- [Docker Smoke Protocol](docker_smoke_protocol.md): canonical container validation procedure.
- [Production Handoff Runbook](production_handoff_runbook.md): operating and handoff expectations.
- [Release Artifact Manifest](release_artifact_manifest.md): package content and persistence boundary.
- [L10.4 Production Handoff Release Notes](release_notes_l10_4_production_handoff.md): latest handoff baseline status.
