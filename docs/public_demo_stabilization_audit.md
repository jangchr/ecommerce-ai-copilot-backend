# L11.3-C Public Demo Stabilization Audit

Date: 2026-05-24

## Scope

This audit records the public demo stabilization state for the Product Mode MVP. It is a documentation-only audit and does not change runtime behavior, workflow routing, Agent prompts, API contracts, grounded quality gates, cost gates, or regression thresholds.

Public demo URL:

https://ecommerce-ai-copilot-backend.onrender.com/

## Documentation Link Audit

| Item | Status | Evidence |
| --- | --- | --- |
| README links Public Demo Quickstart | PASS | `README.md` links `docs/public_demo_quickstart.md`. |
| README links Public Demo Smoke Checklist | PASS | `README.md` links `docs/public_demo_smoke_checklist.md`. |
| Production handoff runbook links Public Demo Quickstart | PASS | `docs/production_handoff_runbook.md` links `docs/public_demo_quickstart.md`. |
| Production handoff runbook links Public Demo Smoke Checklist | PASS | `docs/production_handoff_runbook.md` links `docs/public_demo_smoke_checklist.md`. |
| Render public URL is recorded | PASS | `README.md`, Render setup docs, public demo docs, and public handoff audit reference the Render service URL. |

## Public Deployment Artifact Audit

| Item | Status | Evidence |
| --- | --- | --- |
| Render first deployment smoke document exists | PASS | `docs/render_first_deployment_smoke_20260524.md` exists. |
| Public Product Mode handoff audit exists | PASS | `docs/public_product_mode_handoff_audit.md` exists. |
| Product Mode MVP baseline exists | PASS | `runs/baselines/l11_0_product_mode_mvp/` exists. |
| Docker smoke validation is recorded | PASS | `L10 Manual Docker Smoke #2`, commit `2623da4`, status `Success`. |

## Product Mode Input Boundary

Product Mode stable input remains the 10 local grounded slugs:

- `balsamic_vinegar`
- `printer`
- `women_bras`
- `girls_overalls`
- `protein_powder`
- `phone_case`
- `desk_lamp`
- `baby_stroller`
- `pet_hair_vacuum`
- `skincare_serum`

Amazon URLs are not Product Mode stable inputs. Amazon URLs remain limited to Debug Mode / Amazon Shadow workflows.

## API Boundary Audit

| Boundary | Status |
| --- | --- |
| Product API does not expose `shadow_sources` | PASS |
| Product API does not expose `telemetry_summary` | PASS |
| Product API does not expose `memory_observability` | PASS |
| Debug Mode retains Debug Trace | PASS |
| Debug Mode retains Source Probe | PASS |
| Debug Mode retains Amazon Shadow Summary | PASS |

These boundaries are covered by API contract and live smoke tests, including product response isolation from debug-only observability fields.

## Public Smoke Status

The first public Render deployment smoke passed and is recorded in `docs/render_first_deployment_smoke_20260524.md`:

- Public `/healthz`: PASS
- Public `/`: PASS
- Public `/static/index.html`: PASS
- Public Product Mode UI: PASS
- Public `generate-copilot`: PASS
- Input: `balsamic_vinegar`
- Source: `local_dataset+mock`
- Review confidence: `0.75`
- Evidence alignment: `1.00`
- Grounded: `true`
- Approved: `true`

The later public handoff audit recorded a live recheck caveat: public browser smoke had previously passed, while the Codex environment live recheck was inconclusive due to connection timeout / abrupt close. This is treated as an environment/network caveat, not as a Product Mode regression.

## Conclusion

L11.3 public demo stabilization is complete from the repository and documentation side.

The public demo has a documented quickstart, a cold-start smoke checklist, a recorded Render deployment smoke pass, a Product Mode handoff audit, and a stable Product Mode MVP baseline. Demo operators should use the 10 local grounded slugs and run the public demo smoke checklist shortly before presentations, especially because Render cold starts can affect first request latency.
