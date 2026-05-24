# Product Mode Deployment Handoff Audit

Date: 2026-05-24

Milestone: L11.1-C Product Mode deployment handoff final audit

## Audit Scope

This audit is read-only with respect to runtime behavior. It does not modify `workflow.py`, Agent prompt/schema/reward/routing, grounded gates, cost gates, regression thresholds, or the default `/api/v1/generate-copilot` behavior.

## Baseline And Documentation

| Item | Status | Evidence |
| --- | --- | --- |
| L11.0 Product Mode MVP baseline exists | PASS | `runs/baselines/l11_0_product_mode_mvp/` exists and contains regression reports plus per-category outputs. |
| README records Product Mode MVP demo startup | PASS | README documents `.\l8\Scripts\python.exe main.py` and `http://127.0.0.1:8001/`. |
| README records current Product Mode MVP baseline | PASS | `runs/baselines/l11_0_product_mode_mvp/`. |
| Production handoff runbook records Product Mode MVP status | PASS | Runbook lists the 10 stable slugs, Product Mode boundaries and L11.0 release notes. |
| Docker smoke protocol includes Product frontend smoke | PASS | Protocol validates `/`, `/static/index.html`, `Product Mode is stable`, `balsamic_vinegar` and `Copy Hook`. |

## Docker Smoke

GitHub Actions workflow:

```text
L10 Manual Docker Smoke #2
Commit: 2623da4
Branch: main
Status: Success
Duration: 2m 23s
```

The Docker smoke workflow includes:

- Docker build.
- Container start.
- `/healthz` validation.
- Product Mode frontend checks:
  - `/` returns Product Mode HTML.
  - `/` contains `Product Mode is stable`.
  - `/` contains `balsamic_vinegar`.
  - `/static/index.html` contains `Copy Hook`.
- Startup preflight in container.
- Container fast gate.
- Required asset checks.
- Excluded mutable/secret asset checks.

Result: PASS.

## Product / Debug Boundary

| Boundary | Status |
| --- | --- |
| Product API does not expose `shadow_sources` | PASS |
| Debug API can expose `shadow_sources` | PASS |
| Amazon URL is not Product Mode stable input | PASS |
| Amazon URL remains Debug Mode / Amazon Shadow input | PASS |
| Local 10-category dataset remains Product Mode regression anchor | PASS |

The above API boundaries are covered by fast-gate contract and live-smoke tests.

## Final Validation

Local fast gate:

```text
.\l8\Scripts\python.exe scripts\run_all_tests.py --fast
```

Result: PASS, 95 tests.

## Conclusion

L11.1 Product Mode deployment handoff is complete:

- Product Mode MVP baseline is frozen.
- Static frontend is served locally and inside Docker.
- Docker smoke validates Product frontend routes and copy-control HTML.
- Product/debug API boundaries remain intact.
- Amazon real-source behavior remains debug/shadow-only and outside the stable Product Mode path.
