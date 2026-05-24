# L11.0 Product Mode MVP Release Notes

Date: 2026-05-24

Baseline path: `runs/baselines/l11_0_product_mode_mvp`

## Summary

L11.0 packages the backend as a local Product Mode MVP with a served static frontend, clean product/debug boundaries, browser-validated demo flow and frozen regression baseline.

## Completed Scope

- Static frontend serving ready:
  - `GET /` serves `static/index.html`.
  - `GET /static/index.html` returns the static frontend directly.
- Product Mode UX cleanup ready:
  - Default product input is `balsamic_vinegar`.
  - The page displays the 10 stable local grounded slugs.
  - Amazon URLs are clearly marked as Debug Mode / Amazon Shadow inputs, not stable Product Mode inputs.
  - Product Mode focuses on `insights`, `audience`, `strategy`, `assets`, `evaluation` and `feedback`.
- Browser demo validation ready:
  - Product Mode was browser-validated with `balsamic_vinegar`.
  - Copy controls were validated: `Copy Hook`, `Copy Storyboard`, `Copy Full Markdown`.
  - Debug Trace and Source Probe were browser-validated in Debug Mode.
- Debug trace hidden in Product Mode:
  - Debug Mode Off hides the Debug Trace panel.
  - Product Mode does not show debug telemetry, `shadow_sources` or memory observability.
  - Debug Mode On still supports Debug Trace, Source Probe and Amazon Shadow Summary.

## Regression Results

Fast gate: PASS

- 95 tests passed.

Full gate: PASS

- 10/10 grounded categories passed.
- `review_confidence=0.75` for all categories.
- `review_count=6` for all categories.
- `evidence_alignment=1.0` for all categories.
- `revision_count=0` for all categories.
- `failed_nodes=None`.

Accepted warning:

- `phone_case` grounded CTR dropped by `0.0153`, from `0.0716` to `0.0563`.
- This is accepted because `grounded_ctr=0.0563` remains above the `0.04` absolute grounded gate.

## Cost Gate

- `total_tokens=123942` / `135000`: PASS
- `total_latency_ms=540595.52` / `700000`: PASS
- `storyboard_tokens=34802` / `45000`: PASS
- `strategy_tokens=27387` / `35000`: PASS
- `cognitive_synthesis_tokens=27919` / `35000`: PASS
- `analysis_dopamine_tokens=2571` / `5000`: PASS
- Estimated full-run cost: `$0.0620`

## Memory / Backend

- Final memory backend: `faiss`
- FAISS fallback count: `0`
- Memory records: `385 / 500`
- Remaining capacity: `115`
- Pruned count: `0`

## Boundary Notes

- Product API does not expose `shadow_sources`.
- Debug API can expose `shadow_sources`.
- Amazon Shadow remains debug-only and is not part of the default product generation path.
- Local 10-category dataset remains the regression anchor.
