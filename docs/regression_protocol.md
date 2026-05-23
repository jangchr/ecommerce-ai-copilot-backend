# Regression Protocol

## Purpose

This project treats the local grounded workflow as a regression-tested Agent Runtime. Regression checks protect three properties:

- Grounding quality: local evidence is retrieved and cited in generated scenes.
- Failure safety: weak or ungrounded results do not pass routing or pollute success memory.
- Cost control: full LLM runs remain within the frozen L9.3 cost budget.

## Test Layers

### Fast Gate

Run during ordinary development and automatically in CI on pushes and pull requests:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py --fast
```

In CI:

```bash
python scripts/run_all_tests.py --fast
```

The fast gate runs:

- Python compilation checks.
- `RewardEngine` and memory bucket unit tests.
- Failure behavior tests.
- Failure routing tests.

It does not invoke the LLM API.

### Full Gate

Run before core workflow changes are accepted, after prompt/reward/memory changes, and manually in CI when required:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py
```

The full gate adds the ten-category grounded regression run. It requires `OPENAI_API_KEY` and performs live model calls.

## Grounded Quality Gates

Each category must satisfy:

| Metric | Gate |
| --- | ---: |
| `review_confidence` | `>= 0.70` |
| `review_count` | `>= 5` |
| `evidence_alignment` | `>= 0.50` |
| `grounded_ctr` | `>= 0.04` |
| `revision_count` | `<= 2` |

The local regression categories are:

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

## Diff Gates

Quality comparisons use the frozen L9.2 grounded baseline:

- `grounded_ctr` drop greater than or equal to `0.010`: warning.
- `grounded_ctr` drop greater than or equal to `0.015`: warning when the absolute grounded CTR gate still passes.
- A `grounded_ctr` result below the absolute `0.04` gate remains a failure.
- A category that was fully aligned in the baseline must not drop below the minimum evidence alignment gate.

Warnings are recorded in the Markdown report and CSV summary. Absolute grounding failures and evidence-alignment failures terminate the full gate.

## Cost Gates

The Phase 2D runtime cost baseline is frozen in `runs/baselines/l9_3_phase_2d/`.

Full regression enforces:

| Metric | Warning | Failure |
| --- | ---: | ---: |
| Total tokens | - | `> 135000` |
| Total latency | `> 650000 ms` | `> 700000 ms` |
| Storyboard tokens | - | `> 45000` |
| Strategy tokens | - | `> 35000` |
| Cognitive synthesis tokens | - | `> 35000` |
| Analysis dopamine tokens | - | `> 5000` |
| Failed nodes | - | Any failure |

Latency has a warning band because remote model and network response times vary more than token usage.

## Report Retention

The output directories have fixed meanings:

| Directory | Policy |
| --- | --- |
| `runs/latest/` | Most recent full regression output. May be overwritten by the next full run. |
| `runs/history/<timestamp>/` | Immutable per-run archive produced by each full regression. |
| `runs/baselines/` | Manually frozen stable milestones only. Never overwrite an existing baseline. |

Each full run generates:

- `regression_summary.csv`
- `telemetry_summary.csv`
- `telemetry_aggregate.csv`
- `telemetry_node_aggregate.csv`
- `cost_gate_summary.csv`
- `regression_report.md`
- Per-category API response JSON files

## Freezing A Baseline

Freeze a named baseline only after a full gate has completed and the run is accepted:

```powershell
.\l8\Scripts\python.exe scripts\freeze_baseline.py --name l9_3_phase_2d
```

The script does not overwrite an existing named baseline.

The FAISS recovery and stochastic diff-gate milestone is frozen as:

```powershell
.\l8\Scripts\python.exe scripts\freeze_baseline.py --name l9_6_f_faiss_recovery
```

## CI Workflows

- `.github/workflows/l9_fast.yml`: runs the fast gate on push and pull request.
- `.github/workflows/l9_full_manual.yml`: runs the full gate on manual dispatch and uploads reports as an artifact.

The full workflow requires the repository secret `OPENAI_API_KEY`. Optional configuration:

- `OPENAI_API_BASE` secret for a compatible model endpoint.
- `MODEL_NAME` repository variable.
- `LLM_COST_PER_1K_TOKENS_USD` repository variable for cost reporting.

## API Boundary

- `/api/v1/debug-copilot` is the regression/debug endpoint and may expose evidence, telemetry, routing and world metrics.
- `/api/v1/generate-copilot` is the product-facing endpoint.
- Both endpoints are protected by Pydantic request/response contracts in `schemas/api_contract.py`; product output does not expose internal graph state.

## Source Adapter Activation

Local regression uses `local_review_dataset` and `tiktok_trend_mock` by default.

`ALLOW_REAL_SOURCE_ADAPTERS=false` is the safe default. Setting it to `true` exposes the registered real-source tool names to planning, but the current Amazon, TikTok and Reddit adapters are disabled shells: they make no network requests, return `unavailable`, and retrieval falls back to the local review and mock trend anchors.

## L9.6 Memory / FAISS / Diff Gate Protocol

Memory and vector-backend behavior are observable rather than assumed.

### Manual FAISS Diagnosis

Run the manual backend diagnostic when dependencies, model cache, or execution permissions change:

```powershell
.\l8\Scripts\python.exe scripts\check_faiss_backend.py
```

`check_faiss_backend.py` is intentionally not part of the fast gate. It may need Hugging Face model cache access or network permission, which differs across developer machines and CI runners.

Expected backend behavior:

| Condition | Expected Result |
| --- | --- |
| FAISS dependencies and embedding model are available | `faiss_ok=true`, `backend=faiss`, `fallback_count=0` |
| Model download/cache access is blocked or FAISS initialization fails | `backend=json_fallback` with a non-empty `faiss_error` |

JSON fallback is an allowed operational degradation, provided the failure reason remains visible in telemetry and diagnosis output.

### Memory Growth Health

`MEMORY_MAX_RECORD_COUNT` controls bounded long-term memory growth and defaults to `500`.

The memory observability fields used for diagnosis are:

| Field | Meaning |
| --- | --- |
| `memory_record_count_total` | Current total retained records. |
| `memory_remaining_capacity` | Remaining records before the configured cap. |
| `memory_pruned_count` | Count of oldest records removed when capacity is exceeded. |
| `faiss_fallback_count` | Number of FAISS initialization or access degradations. |
| `faiss_fallback_trace` | Bounded, deduplicated fallback reasons and operation counts. |

These fields are emitted in `telemetry_summary.csv` and summarized in `telemetry_node_aggregate.csv`, including the final `analytics_memory` snapshot after each memory write.

### Stochastic Diff Handling

The absolute grounded quality gates remain hard requirements. Baseline comparison exists to reveal drift, not to reject otherwise grounded live model samples:

- Any absolute gate failure still fails full regression.
- If `grounded_ctr` is still `>= 0.04`, a drop relative to baseline is preserved as `WARN`, including drops beyond `CTR_FAIL_DROP`.
- The warning remains present in `regression_summary.csv` and `regression_report.md` for review.
