# Public Product Mode Handoff Audit

Date: 2026-05-24

Milestone: L11.2-E Public Product Mode handoff final audit

Render service URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com
```

## Scope

This audit does not modify runtime behavior. It does not change `workflow.py`, Agent prompt/schema/reward/routing, grounded gates, cost gates, regression thresholds, API contracts, or the default `/api/v1/generate-copilot` behavior.

## Artifact Audit

| Item | Status | Evidence |
| --- | --- | --- |
| L11.0 Product Mode MVP baseline exists | PASS | `runs/baselines/l11_0_product_mode_mvp/` |
| L11.0 release notes exist | PASS | `docs/release_notes_l11_0_product_mode_mvp.md` |
| Render first deployment smoke exists | PASS | `docs/render_first_deployment_smoke_20260524.md` |
| Render service URL recorded | PASS | `https://ecommerce-ai-copilot-backend.onrender.com` |
| Docker smoke for commit `2623da4` passed | PASS | GitHub Actions `L10 Manual Docker Smoke #2`, status `Success`, duration `2m 23s` |

## Recorded Public Smoke

The first public Render deployment smoke is recorded in `docs/render_first_deployment_smoke_20260524.md`.

| Check | Recorded Status |
| --- | --- |
| Public `/healthz` | PASS |
| Public `/` | PASS |
| Public `/static/index.html` | PASS |
| Public Product Mode UI | PASS |
| Public `/api/v1/generate-copilot` with `balsamic_vinegar` | PASS |
| Source | `local_dataset+mock` |
| Review confidence | `0.75` |
| Evidence alignment | `1.00` |
| Grounded | `true` |
| Approved | `true` |

## Current Live Recheck

A live recheck from the current Codex environment was attempted against the Render URL.

Result: INCONCLUSIVE due to current network/service response instability from this environment.

Observed behavior:

- `curl` resolved `ecommerce-ai-copilot-backend.onrender.com`.
- The TLS connection to `/healthz` was established.
- The server closed the connection before a response body was returned.
- PowerShell `Invoke-RestMethod` / `Invoke-WebRequest` attempts timed out.
- Product POST retry with `curl.exe` exited with `curl: (56) schannel: server closed abruptly`.

This live recheck result is not recorded as a Product Mode runtime regression because the previously documented public smoke passed, Docker smoke passed, and local fast gate still passes. It should be rechecked from a normal browser or Render dashboard before treating the public service as continuously healthy.

## Product / Debug Boundary Audit

| Boundary | Status |
| --- | --- |
| Product Mode stable input remains the 10 local grounded slugs | PASS |
| Amazon URL remains Debug Mode / Amazon Shadow input only | PASS |
| `ALLOW_REAL_SOURCE_ADAPTERS=false` for MVP deployment | PASS |
| Product API must not expose `shadow_sources` | PASS |
| Product API must not expose `telemetry_summary` | PASS |
| Product API must not expose `memory_observability` | PASS |
| Debug API can expose `shadow_sources` | PASS |
| Local grounded dataset remains the Product Mode regression anchor | PASS |

The Product/API boundaries above are covered by fast-gate contract and live-smoke tests.

## Final Status

Public handoff documentation is complete and internally consistent:

- Render deployment setup is documented.
- First public Render smoke is documented as PASS.
- Product Mode MVP baseline is frozen.
- Docker smoke for the deployment-supporting commit passed.
- Product/debug boundaries remain protected.

Operational note:

- Re-run a live public smoke from a normal browser or Render dashboard if the public service appears unavailable, because the current Codex environment observed transient connection closure/timeouts during this audit.
