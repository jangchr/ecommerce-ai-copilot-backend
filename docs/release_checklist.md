# Release Checklist

Use this checklist before freezing or shipping a release of the grounded ecommerce creative agent backend.

## 1. Required Preflight Commands

Run these commands from the `backend` directory, in order:

- [ ] Verify environment configuration, required datasets and frozen baselines:

  ```powershell
  .\l8\Scripts\python.exe scripts\check_env.py
  ```

- [ ] Diagnose vector memory backend health:

  ```powershell
  .\l8\Scripts\python.exe scripts\check_faiss_backend.py
  ```

- [ ] With the deployed or locally started API running, verify the lightweight health endpoint:

  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz" -Method GET
  ```

  Confirm that `status` is `ok`, `service` is `grounded-ecommerce-creative-agent`, `stable_baseline` is `l9_9_stable`, and the HTTP response includes `X-Request-ID`.

- [ ] Verify observability response boundaries with an API smoke request:
  - Confirm `/api/v1/debug-copilot` body `request_id` equals its response header `X-Request-ID`.
  - Confirm `/api/v1/debug-source-probe` body `request_id` equals its response header `X-Request-ID`.
  - Confirm `/api/v1/generate-copilot` response body contains neither `request_id` nor `telemetry_summary`; correlation is header-only for the product endpoint.

- [ ] Run the fast regression gate:

  ```powershell
  .\l8\Scripts\python.exe scripts\run_all_tests.py --fast
  ```

- [ ] Run the full grounded regression gate:

  ```powershell
  .\l8\Scripts\python.exe scripts\run_all_tests.py
  ```

## 2. Required Report Review

After the full regression completes, inspect each latest-run artifact:

- [ ] `runs/latest/regression_summary.csv`
  - Confirm all categories pass the absolute grounded quality requirements.
  - Review any `diff_status` or `diff_warning` values.

- [ ] `runs/latest/telemetry_node_aggregate.csv`
  - Confirm no failed node is recorded.
  - Review node token and latency distribution for unexpected shifts.
  - Review memory backend and FAISS/fallback observability where present.

- [ ] `runs/latest/cost_gate_summary.csv`
  - Confirm no metric has a hard `FAIL` status.
  - Record any latency warning for release notes or follow-up.

- [ ] `runs/latest/regression_report.md`
  - Confirm the summary agrees with the CSV artifacts.
  - Note accepted warnings and their explanation.

## 3. Allowed Release Conditions

A release may proceed with these visible conditions, provided no blocking item below is present:

- [ ] A `grounded_ctr` baseline-diff warning is acceptable when its absolute grounded gate still passes.
- [ ] `total_latency_ms` may exceed the warning threshold while remaining below the failure threshold.
- [ ] In a restricted environment, `backend=json_fallback` is acceptable when the diagnostic and telemetry include a non-empty `faiss_error`.

These allowances are for observable environmental or stochastic variance. They do not waive absolute grounded quality or hard cost requirements.

## 4. Release Blockers

Do not freeze or release if any item below is true:

- [ ] `scripts/run_all_tests.py --fast` fails.
- [ ] `scripts/run_all_tests.py` full regression fails.
- [ ] Any absolute grounded quality gate fails.
- [ ] Any cost gate reports a hard failure.
- [ ] `failed_nodes` is not `None` or otherwise records node failure.
- [ ] `/api/v1/generate-copilot` exposes `data.debug` or another internal debug-state field.
- [ ] `/api/v1/generate-copilot` exposes `request_id` or `telemetry_summary` in its response body.
- [ ] A debug response body `request_id` does not match its `X-Request-ID` response header.
- [ ] The frontend issues a `/api/v1/debug-copilot` request while **Debug Mode** is off.

For frontend boundary validation, follow the [Frontend Smoke Protocol](frontend_smoke_protocol.md). For endpoint examples and response boundaries, see [API Examples](api_examples.md).
For deployment-specific secrets, storage persistence, cache and endpoint exposure policies, see the [Deployment Environment Matrix](deployment_environment_matrix.md).

## 5. Baseline Freeze Conditions

Freeze a new release baseline only when all of the following are satisfied:

- [ ] Full regression has passed in consecutive accepted runs.
- [ ] The cost gate passes without hard failure.
- [ ] No new hard failure has appeared in grounding, routing, API boundary or memory/backend health.
- [ ] Any accepted warnings have been reviewed and recorded.

After those checks, freeze the accepted latest full run:

```powershell
.\l8\Scripts\python.exe scripts\freeze_baseline.py --name <release_name>
```

Never overwrite an existing baseline directory. Current stable baseline:

```text
runs/baselines/l9_9_stable/
```

Historical release candidate baseline:

```text
runs/baselines/l9_9_rc1/
```

## 6. Release Sign-Off Record

Record the following with the release decision:

| Item | Value |
| --- | --- |
| Release name |  |
| Date |  |
| Environment preflight status |  |
| FAISS backend / fallback status |  |
| Fast gate status |  |
| Full gate status |  |
| Accepted warnings |  |
| Baseline frozen path |  |

## Related Documents

- [Architecture Map](architecture_map.md): runtime layers and data-flow boundaries.
- [Regression Protocol](regression_protocol.md): quality, cost, memory and baseline policy.
- [Frontend Smoke Protocol](frontend_smoke_protocol.md): Debug Mode and product/debug request separation.
- [API Examples](api_examples.md): executable endpoint requests and response-field reference.
- [L9.9-RC1 Release Notes](release_notes_l9_9_rc1.md): accepted RC1 evidence, costs and warnings.
- [L9.9-Stable Release Notes](release_notes_l9_9_stable.md): final stable validation, cost and memory status.
- [L10.4 Production Handoff Release Notes](release_notes_l10_4_production_handoff.md): deployment handoff validation, accepted warning, observability and frozen handoff baseline.
- [Deployment Environment Matrix](deployment_environment_matrix.md): environment variables, persistence, artifact retention and debug-probe policy by deployment tier.
- [Production Handoff Runbook](production_handoff_runbook.md): operator startup order, persistence strategy, observability boundaries and failure response.
