# L10.10 Amazon Shadow Observability Release Notes

## Scope

This release refresh records the Amazon shadow-source work completed after the L10.4 production handoff baseline. It does not change `/api/v1/generate-copilot` default behavior, workflow retrieval, Agent prompts, reward logic, memory policy, grounded gates, cost gates or regression thresholds.

Amazon remains debug-only and shadow-only. It is not promoted to `amazon_primary`.

## Completed Milestones

| Milestone | Status |
| --- | --- |
| L10.7 Amazon debug-only source probe | Complete |
| L10.8 Amazon shadow mode | Complete |
| L10.9 Amazon shadow evaluation | Complete |
| L10.10 Amazon shadow observability | Complete |

## Final Shadow Evaluation Result

After retry, error classification and propagation hardening, probe-only evaluation reached:

| Metric | Value |
| --- | ---: |
| Probe-only success after hardening | 19/20 |
| Safety failure count | 0 |
| Product API called | false |
| Debug Copilot called in probe-only | false |
| `memory_write_allowed` | false |
| `used_for_generation` | false |

The final evaluation also confirmed that `WinError 10061` no longer leaks into generic `url_error`; it is classified as `connection_refused`.

## Observability Surface

Debug UI Amazon Shadow Summary now exposes:

- provider status
- source confidence
- product title
- rating
- review count
- evidence preview count
- bullet point count
- category hint
- latency
- error type
- retry count
- memory write allowed
- used for generation

The Product API does not expose `shadow_sources`.

## Safety Decision

Amazon shadow source quality is strong enough for continued debug-only observation and UX work.

Do not enter `amazon_primary` yet.

Promotion would require a separate design review, broader live URL coverage, repeated stability checks, memory non-pollution proof and explicit acceptance that local grounded datasets remain the regression anchor.

## Related Documents

- [Amazon Shadow Mode Plan](amazon_shadow_mode_plan.md)
- [Amazon Shadow Evaluation Plan](amazon_shadow_evaluation_plan.md)
- [Amazon Shadow Evaluation Final Report](amazon_shadow_evaluation_final_report.md)
- [Frontend Smoke Protocol](frontend_smoke_protocol.md)
