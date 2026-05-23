# L9.9-RC1 Release Notes

## Release Candidate

```text
L9.9-RC1 release candidate baseline ready
Baseline: runs/baselines/l9_9_rc1
```

This release candidate freezes the grounded local-data runtime after release-checklist validation of environment readiness, vector-memory health, fast regression, full grounded regression and cost controls.

## Validation Summary

| Check | Result |
| --- | --- |
| Baseline path | `runs/baselines/l9_9_rc1` |
| `check_env` status | `PASS` |
| FAISS backend | `faiss` |
| `faiss_fallback_count` | `0` |
| Fast gate | `PASS` |
| Full gate | `PASS` |
| Grounded categories | `10/10` passed |
| Evidence alignment | `1.0` for all categories |
| Failed nodes | `None` |

## Accepted Warnings

The following baseline-diff warnings are accepted because each result remains above the absolute grounded CTR gate:

| Category | Grounded CTR | Delta From Baseline |
| --- | ---: | ---: |
| `printer` | `0.0548` | `-0.0100` |
| `girls_overalls` | `0.0519` | `-0.0110` |
| `skincare_serum` | `0.0504` | `-0.0109` |

No warning represents an absolute grounded-quality failure.

## Cost Gate Summary

| Metric | Value | Result |
| --- | ---: | --- |
| `total_tokens` | `128264` | `PASS` |
| `total_latency_ms` | `594954` | `PASS` |
| `storyboard_tokens` | `34629` | `PASS` |
| `strategy_tokens` | `25717` | `PASS` |
| `cognitive_synthesis_tokens` | `28329` | `PASS` |
| `analysis_dopamine_tokens` | `2578` | `PASS` |
| Estimated full-run cost | `$0.0641` | Recorded |

All cost-gate hard limits passed; no latency warning was required for this run.

## Memory And FAISS Summary

| Metric | Value |
| --- | ---: |
| Records retained | `297 / 500` |
| Remaining capacity | `203` |
| Pruned count | `0` |
| Final backend | `faiss` |
| FAISS fallback count | `0` |

Memory remained below its configured capacity cap and no pruning or fallback was required.

## Frozen Artifacts

The RC baseline contains the report and category outputs required for later comparison:

- `runs/baselines/l9_9_rc1/regression_report.md`
- `runs/baselines/l9_9_rc1/regression_summary.csv`
- `runs/baselines/l9_9_rc1/telemetry_node_aggregate.csv`
- `runs/baselines/l9_9_rc1/cost_gate_summary.csv`

## Next Ship Step

Before freezing a stable release baseline, run the full release checklist again. If the subsequent full regression passes with no new hard failures and cost gates remain satisfied, freeze:

```powershell
.\l8\Scripts\python.exe scripts\freeze_baseline.py --name l9_9_stable
```
