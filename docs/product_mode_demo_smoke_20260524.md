# Product Mode Demo Smoke - 2026-05-24

## Scope

This smoke execution follows `docs/product_mode_demo_protocol.md`. It does not change `/api/v1/generate-copilot`, workflow retrieval, Agent prompts, reward logic, grounded gates, cost gates or regression thresholds.

## Environment

Backend command:

```powershell
.\l8\Scripts\python.exe main.py
```

Backend status:

- Uvicorn started on port `8001`.
- API endpoints responded successfully.

UI open target:

```text
http://127.0.0.1:8001
```

Result:

- `http://127.0.0.1:8001` returned `404 Not Found`.
- `/static/index.html` also returned `404 Not Found`.
- Because this task explicitly forbids modifying `main.py`, no route or static-file serving behavior was changed.
- Static frontend source was inspected directly from `static/index.html` for Product Mode controls and guard logic.
- This 404 was accepted as the follow-up target for L11.0-D static frontend serving fix.

## Product Mode Test

Product input:

```text
balsamic_vinegar
```

Product API:

```text
POST /api/v1/generate-copilot
```

Result:

| Check | Status |
| --- | --- |
| API response status | PASS |
| `insights` present | PASS |
| `audience` present | PASS |
| `strategy` present | PASS |
| `assets` present | PASS |
| `evaluation` present | PASS |
| `feedback` present | PASS |
| source type | `local_dataset+mock` |
| grounded | `true` |
| approved | `true` |
| Product response excludes debug fields | PASS |

Product response did not expose:

- `telemetry`
- `telemetry_summary`
- `memory_observability`
- `shadow_sources`
- `debug`

## Copy Buttons

Static frontend source includes:

- `Copy Hook`
- `Copy Storyboard`
- `Copy Full Markdown`
- `function copyHook()`
- `function copyStoryboard()`
- `function copyFullMarkdown()`

Product API returned enough material for all copy actions:

- hook text present
- storyboard present
- feedback present

Clipboard interaction was not executed in browser because the UI is not currently served at `http://127.0.0.1:8001`.

## Debug Mode Off Boundary

API-only validation invoked only:

```text
POST /api/v1/generate-copilot
```

Static frontend source contains guards that keep Debug Mode Off isolated:

- Source Probe tools are hidden when Debug Mode is off.
- Amazon Shadow option is hidden when Debug Mode is off.
- Amazon Shadow is unchecked when Debug Mode is off.
- The page does not reference `data.debug`.

Expected boundary:

| Boundary | Status |
| --- | --- |
| no `/api/v1/debug-copilot` in Product Mode API-only run | PASS |
| no `/api/v1/debug-source-probe` in Product Mode API-only run | PASS |
| no Amazon Shadow in Product Mode API-only run | PASS |
| source guard present in frontend source | PASS |

## Debug Mode On Boundary

Debug API:

```text
POST /api/v1/debug-copilot
```

Result:

- Debug Trace fields were present.
- `shadow_sources` was `{}` in local mode.

Source Probe API:

```text
POST /api/v1/debug-source-probe
```

Result:

- Source Probe returned provider results.
- Providers included:
  - `amazon_review_api`
  - `reddit_review_api`
  - `tiktok_trend_api`
- `memory_write_allowed=false`

Amazon Shadow debug API:

```text
POST /api/v1/debug-copilot
real_source_mode=amazon_shadow
```

Result:

- `shadow_sources.amazon_review_api` was present.
- `memory_write_allowed=false`
- `used_for_generation=false`
- Product API was not called by the probe-only path.

## UI Issues

One UI-serving issue was found:

```text
http://127.0.0.1:8001 -> 404 Not Found
```

The backend currently exposes API endpoints but does not serve the frontend at the root URL. This blocks true browser-level verification of Product Mode copy buttons and Network panel behavior through `http://127.0.0.1:8001`.

Recommended next step:

- Add a separate L11 task to decide whether the backend should serve `static/index.html` at `/` or whether the demo protocol should explicitly use a separate static-file preview.
- Do not fold that route change into this smoke execution because this task forbids modifying `main.py`.

## Overall Result

| Area | Status |
| --- | --- |
| Backend/API Product Mode | PASS |
| Product response field contract | PASS |
| Product/debug body isolation | PASS |
| Debug Trace API | PASS |
| Source Probe API | PASS |
| Amazon Shadow debug boundary | PASS |
| Static frontend controls and guards | PASS |
| Browser-open demo at `http://127.0.0.1:8001` | BLOCKED by 404 |

Conclusion:

Product Mode backend behavior and frontend source boundaries are healthy. The remaining blocker is a demo-serving mismatch: the documented local UI URL is not currently served by the backend.
