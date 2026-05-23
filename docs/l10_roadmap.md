# L10.0 Roadmap Planning

## Starting Point

L10 starts from the frozen stable baseline:

```text
L9.9-Stable final release baseline ready
Baseline: runs/baselines/l9_9_stable
```

The L9 stable line already protects local grounded regression, product/debug API separation, bounded observable memory, FAISS fallback visibility and fast/full release gates. L10 work must extend those boundaries without weakening them.

## Guiding Principles

- Keep `local_review_dataset` and the frozen grounded suite as the regression anchor.
- Treat real external sources as optional, observable inputs until their reliability and data policies are proven.
- Preserve the product/debug API boundary: product output remains clean; diagnostics remain explicit.
- Require measurable operational evidence before promoting experimental behavior into a default runtime path.

## A. L10.1 Debug-Only Real Source Adapter Probe

### Goal

Evaluate Amazon, TikTok and Reddit source integrations without changing the default product runtime or contaminating established memory.

### Scope

- Implement real-source adapter probing only behind **Debug Mode** or an explicit environment feature flag.
- Keep the normal product execution path on the stable local/mock source configuration by default.
- Emit probe telemetry sufficient to judge availability, latency, source confidence, error patterns and fallback behavior.

### Safety Rules

| Requirement | Expected Behavior |
| --- | --- |
| Activation | Probe runs only in debug context or when an explicit env flag opts in. |
| Product runtime | `/api/v1/generate-copilot` default behavior remains on safe grounded anchors. |
| Fallback | Failure, timeout or insufficient evidence returns to `local_review_dataset` and mock trend behavior. |
| Memory isolation | Probe outcomes do not write to success memory unless a future, separately reviewed promotion policy exists. |
| Regression | Local datasets remain the fixed anchor for fast/full grounded comparison. |

### Deliverables

- Provider-specific configuration and credential handling for probe mode.
- Debug-only source result and fallback trace visibility.
- Probe fixtures/tests that do not require live APIs for standard regression.
- A promotion review document before any source may influence product defaults.

### Exit Criteria

- Real-source failures are observable and cannot break stable product behavior.
- No success-memory pollution occurs from probe-only source evidence.
- Stable local grounded regression remains unchanged and passing.

## B. L10.2 Deployment Hardening

### Goal

Package the stable runtime for repeatable deployment while keeping startup safety and artifact handling explicit.

### Work Items

| Item | Purpose |
| --- | --- |
| `Dockerfile` | Build a pinned, reproducible runtime image around the verified Python and dependency set. |
| Health endpoint | Expose lightweight service/process readiness without triggering an LLM workflow. |
| Environment matrix | Document development, CI, staging and production settings, secrets, adapter flags and memory storage choices. |
| Startup preflight | Run or integrate environment checks for required files, dependencies, baseline availability and configured feature flags. |
| Artifact retention policy | Specify retention, persistence and access rules for `runs/`, memory storage, baselines and operational logs. |

### Deployment Constraints

- Startup health must not silently enable real source adapters.
- Deployment packaging must preserve `.env`/secret separation.
- Regression baseline artifacts must remain versioned independently from ephemeral latest/history outputs.
- Any persistent memory volume must retain capacity controls and observability.

### Exit Criteria

- A clean deployment can start, report health and run the approved fast gate.
- Environment expectations and artifact lifecycle are documented for each deployment target.
- Default product behavior remains equivalent to the L9.9 stable baseline.

## C. L10.3 Production Observability

### Goal

Make production behavior traceable at request and runtime levels without exposing internal diagnostics through product responses.

### Work Items

| Capability | Purpose |
| --- | --- |
| `request_id` | Correlate API request, workflow trace, adapter calls, memory actions and report/export records. |
| Structured logs | Replace ad hoc terminal-only interpretation with machine-readable operational events. |
| Per-request telemetry export | Capture node latency, token usage, estimated cost, revisions, grounding metrics and final status. |
| Source adapter failure metrics | Aggregate adapter timeout/unavailable/fallback rates and confidence distribution. |
| Memory backend status | Surface FAISS/JSON backend state, fallback traces, capacity, pruning and retrieval/write outcomes. |
| Regression artifact summary | Publish compact health summaries derived from full regression reports and frozen comparisons. |

### Data Boundary

- Debug and operational exports may contain evidence and telemetry under appropriate access controls.
- Product API responses remain limited to product-facing output.
- Logs and exports must avoid raw secrets and should use bounded evidence previews where appropriate.

### Exit Criteria

- A single `request_id` traces an execution across API, adapters, workflow, memory and telemetry.
- Source and memory degradations can be detected without manually inspecting raw state.
- Production observability does not weaken API boundaries or release gates.

## Explicit Prohibitions

The following actions are out of scope for L10 unless separately reviewed after measured probe results:

- Do **not** directly connect real external data sources to the default product runtime.
- Do **not** lower the absolute grounded quality gate, including the `grounded_ctr >= 0.04` requirement.
- Do **not** expose debug telemetry, graph state or memory internals through `/api/v1/generate-copilot`.
- Do **not** remove or replace the local dataset regression anchor.

## Proposed Sequence

```text
L10.0 roadmap planning
  -> L10.1 debug-only real source adapter probe
  -> L10.2 deployment hardening
  -> L10.3 production observability
```

Each phase should begin from `runs/baselines/l9_9_stable`, keep fast/full regression available, and introduce new default behavior only after an explicit promotion decision.

## References

- [README](../README.md)
- [Architecture Map](architecture_map.md)
- [Regression Protocol](regression_protocol.md)
- [Release Checklist](release_checklist.md)
- [L9.9-Stable Release Notes](release_notes_l9_9_stable.md)
