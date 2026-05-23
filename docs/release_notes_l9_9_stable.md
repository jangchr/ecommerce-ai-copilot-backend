# L9.9-Stable Release Notes

## Stable Release

```text
L9.9-Stable final release baseline ready
Baseline: runs/baselines/l9_9_stable
```

This stable baseline was frozen after the release candidate and a subsequent full release-checklist validation both passed without hard blockers.

## Validation Summary

| Check | Result |
| --- | --- |
| Baseline path | `runs/baselines/l9_9_stable` |
| `check_env` status | `PASS` |
| FAISS backend | `faiss` |
| `faiss_fallback_count` | `0` |
| Fast gate | `PASS`, `41` unit tests |
| Full gate | `PASS`, `10/10` categories |
| Evidence alignment | `1.0` for all categories |
| Failed nodes | `None` |

## Accepted Warning

One baseline-diff warning was accepted because it remains above the absolute grounded CTR gate:

| Category | Grounded CTR | Delta From Baseline | Decision |
| --- | ---: | ---: | --- |
| `phone_case` | `0.0545` | `-0.0171` | Accepted: above the `0.04` absolute gate |

No absolute grounded-quality failure occurred.

## Cost Summary

| Metric | Value | Result |
| --- | ---: | --- |
| `total_tokens` | `123517` | `PASS` |
| `total_latency_ms` | `542513` | `PASS` |
| `storyboard_tokens` | `34368` | `PASS` |
| `strategy_tokens` | `27527` | `PASS` |
| `cognitive_synthesis_tokens` | `28178` | `PASS` |
| `analysis_dopamine_tokens` | `2583` | `PASS` |
| Estimated full-run cost | `$0.0618` | Recorded |

## Memory Summary

| Metric | Value |
| --- | ---: |
| Records | `307 / 500` |
| Remaining capacity | `193` |
| Pruned count | `0` |
| Final backend | `faiss` |
| Fallback count | `0` |

Memory remained within its configured capacity and did not require pruning or backend fallback.

## Frozen Artifacts

The stable baseline contains the final comparison artifacts:

- `runs/baselines/l9_9_stable/regression_report.md`
- `runs/baselines/l9_9_stable/regression_summary.csv`
- `runs/baselines/l9_9_stable/telemetry_node_aggregate.csv`
- `runs/baselines/l9_9_stable/cost_gate_summary.csv`

## Release Position

`l9_9_stable` is the current stable release baseline. `l9_9_rc1` remains the release candidate predecessor, and `l9_6_f_faiss_recovery` remains an earlier historical stable milestone.
