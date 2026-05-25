# Frontend Smoke Protocol

## Purpose

This protocol validates the frontend/API boundary of the Agent Debugger without changing workflow behavior or requiring browser automation. It confirms that product rendering and observability rendering remain separated.

## Scope

The page under test is `static/index.html`.

For a product-demo-oriented walkthrough, use the [Product Mode Demo Protocol](product_mode_demo_protocol.md).

The API surfaces have distinct responsibilities:

| Endpoint | Purpose | Frontend Use |
| --- | --- | --- |
| `/api/v1/generate-copilot` | Product-facing response | Evidence, strategy, scene graph and reward presentation |
| `/api/v1/debug-copilot` | Debug/observability response | Raw debug trace, telemetry, world metrics, memory observability and routing state |
| `/api/v1/debug-source-probe` | Debug-only real-source shell probe | Provider status, confidence, latency and fallback telemetry |

## Prerequisites

1. Start the backend:

   ```powershell
   .\l8\Scripts\python.exe main.py
   ```

2. Open `static/index.html` in the frontend preview used for local development.
3. Open the browser Network panel and clear existing requests before each check.

## Smoke Test: Product Mode Slug UX

1. Turn **Debug Mode** off.
2. Confirm the public landing headline says: `Generate TikTok creative strategy from grounded ecommerce review insights.`
3. Confirm the input helper says the public demo uses 10 stable local grounded product categories and recommends `balsamic_vinegar`.
4. Confirm the page shows quick-pick controls, including **Try balsamic_vinegar**.
5. Confirm quick-pick controls only fill the input and do not automatically call the API.
6. Confirm the warning says not to use Amazon URLs in Product Mode and that Amazon URLs are only for Debug Mode / Amazon Shadow.
7. Enter one stable slug, for example `balsamic_vinegar`.
8. Run the workflow.

Expected results:

- The page clearly presents itself as a grounded ecommerce creative agent public demo.
- The page explains that Amazon URLs are for Debug Mode / Amazon Shadow only.
- The visible slug list includes `balsamic_vinegar`, `printer`, `women_bras`, `girls_overalls`, `protein_powder`, `phone_case`, `desk_lamp`, `baby_stroller`, `pet_hair_vacuum` and `skincare_serum`.
- Product sections read like a TikTok creative brief: Evidence Snapshot, Target Audience, Creative Strategy, Hook, Storyboard, Evaluation and Copy Actions.
- Product Mode does not display telemetry, `shadow_sources` or memory observability.
- Product Mode does not display a `DEBUG TRACE` / Debug Trace panel while Debug Mode is off.
- Copy controls are visible:
  - `Copy Hook`
  - `Copy Storyboard`
  - `Copy Full Markdown`
  - `Translate to Chinese`
  - `Copy Chinese Translation`

## Smoke Test: Product Mode Result Readability

1. Turn **Debug Mode** off.
2. Run the workflow with `balsamic_vinegar`.
3. Inspect the rendered Product Mode result.

Expected results:

- Evidence Snapshot displays a compact source badge, review/trend confidence and short evidence quote list.
- Target Audience is visible without raw cognitive state.
- Creative Strategy highlights Core Hook Strategy, Emotional Trigger and CTA Logic.
- Hook is visible as a first-class output.
- Storyboard renders Scene 1 / Scene 2 / Scene 3 / Scene 4 style shooting-script blocks with Visual, Narration and Evidence.
- Evaluation displays Approved, Grounded, Risk Level and rationale in user-facing language.
- Raw telemetry, `shadow_sources`, `memory_observability` and raw internal state remain hidden unless Debug Mode is on.

## Smoke Test: Product Translation

1. Turn **Debug Mode** off.
2. Run Product Mode with `balsamic_vinegar`.
3. Click **Translate to Chinese**.
4. Inspect the Network panel and the Product Mode result.

Expected results:

- One translation request is issued: `POST /api/v1/translate-output`.
- The request body is based on Product Mode full Markdown output.
- No `POST /api/v1/debug-copilot` request is required.
- No `POST /api/v1/debug-source-probe` request is issued.
- No Amazon Shadow request is issued.
- The UI shows `Translating...` during translation.
- A `Chinese Translation` block appears after success.
- `Copy Chinese Translation` becomes usable after translation succeeds.
- Translation failure displays a friendly error while keeping the original English result visible.
- The page still does not reference `data.debug`.

## Smoke Test: Section-Level Product Translation

1. Turn **Debug Mode** off.
2. Run Product Mode with `balsamic_vinegar`.
3. Click **Translate this section** under Evidence Snapshot.
4. Click **Translate this section** under Storyboard.
5. Use **Copy section translation** for one translated section.

Expected results:

- Section translation uses `POST /api/v1/translate-output`.
- The clicked section shows `Translating this section...` while the request is in flight.
- The translated text appears only beneath that section.
- Other Product Mode sections remain unchanged.
- The original English section remains visible.
- Section translation does not automatically run on page load or generation.
- A new workflow run clears old section translations.
- The section text source is Product Mode visible text only; it must not include Debug Trace, telemetry, `telemetry_summary`, `shadow_sources`, `memory_observability`, Source Probe data or Amazon Shadow Summary.

## Smoke Test: Debug Mode Off

1. Turn **Debug Mode** off.
2. Enter a test product URL.
3. Run the workflow.
4. Inspect the Network panel.

Expected results:

- Exactly the product request is issued by this run: `POST /api/v1/generate-copilot`.
- No `POST /api/v1/debug-copilot` request is issued.
- No `POST /api/v1/debug-source-probe` request is issued.
- Amazon Shadow is hidden/disabled and no `real_source_mode=amazon_shadow` request is issued.
- Evidence, Strategy, Scene Graph and Reward sections render from the product response.
- The Debug Trace section is hidden and does not show debug-only trace text or internal graph state.
- The **Run Source Probe** control is hidden and cannot be triggered.

## Smoke Test: Debug Mode On

1. Turn **Debug Mode** on.
2. Clear the Network panel.
3. Run the workflow.
4. Inspect the Network panel and Debug Trace section.

Expected results:

- A product request is issued: `POST /api/v1/generate-copilot`.
- An additional debug request is issued: `POST /api/v1/debug-copilot`.
- Product sections continue to render from the product response.
- Debug Trace renders observability returned by the debug response, including applicable fields:
  - `evidence`
  - `world_metrics`
  - `telemetry`
  - `memory_observability`
  - `revision_count`
  - `regenerate_node`

## Smoke Test: Amazon Shadow Observability

1. Turn **Debug Mode** on.
2. Turn **Amazon Shadow** on.
3. Enter an Amazon product URL, for example `https://www.amazon.com/dp/B00QIIMCCW`.
4. Run the workflow.
5. Inspect the Debug Trace panel.

Expected results:

- The product request still calls only `POST /api/v1/generate-copilot` and does not receive `shadow_sources` in the product response body.
- The debug request calls `POST /api/v1/debug-copilot` with `real_source_mode=amazon_shadow`.
- The Debug Trace panel displays an `Amazon Shadow Summary` with:
  - `Shadow Provider Status`
  - `Shadow Source Confidence`
  - `Shadow Product Title`
  - `Shadow Rating`
  - `Shadow Review Count`
  - `Shadow Evidence Preview Count`
  - `Shadow Bullet Points Count`
  - `Shadow Category Hint`
  - `Shadow Latency Ms`
  - `Shadow Error Type`
  - `Shadow Retry Count`
  - `Shadow Memory Write Allowed`
  - `Shadow Used For Generation`
- If `error_type` exists, the panel displays `Shadow Error Type` explicitly instead of relying only on raw error text.
- `Shadow Memory Write Allowed` remains `false`.
- `Shadow Used For Generation` remains `false`.
- Existing product output remains unchanged if Amazon shadow probing fails.
- Turning **Debug Mode** off hides and disables Amazon Shadow; it must not trigger shadow source calls.

## Smoke Test: Source Probe In Debug Mode

1. Turn **Debug Mode** on.
2. Click **Run Source Probe**.
3. Inspect the Network panel and the Source Probe output.

Expected results:

- One `POST /api/v1/debug-source-probe` request is issued only after clicking the button.
- The request sends `providers: []` and `debug_only: true`, leaving default real-shell selection to the backend.
- Provider rows include `amazon_review_api`, `tiktok_trend_api` and `reddit_review_api`.
- Each provider displays `provider`, `status`, `source_confidence`, `latency_ms`, `error` and `evidence_preview`.
- Telemetry displays `provider_count`, `success_count`, `disabled_count`, `unavailable_count`, `error_count`, `total_latency_ms` and `fallback_required`.
- The probe does not execute `local_review_dataset` or `tiktok_trend_mock`, does not write memory, and disabled shells make no external API call.

## Smoke Test: Amazon Probe Display

1. Turn **Debug Mode** on.
2. Enter an Amazon balsamic vinegar URL, for example `https://www.amazon.com/dp/B00QIIMCCW`.
3. Click **Run Source Probe**.
4. Inspect the `amazon_review_api` provider row.

Expected results when the Amazon probe succeeds:

- `evidence_preview` displays short visible review snippets.
- Amazon metadata fields are visible:
  - `Amazon Product Title`
  - `Amazon Rating`
  - `Amazon Review Count`
  - `Amazon Price`
  - `Amazon Category Hint`
  - `Amazon Bullet Points`
- `fallback_required` is `false` when `source_confidence >= 0.70`.
- `memory_write_allowed` remains `false` in the debug-source-probe response.

Expected results when Amazon blocks, redirects or parsing fails:

- The provider row displays `status` as `unavailable` or `error`.
- `Amazon Data Warnings` or `Amazon Adapter Error` explains the failure.
- Existing product output remains unchanged.
- No product rerun is triggered by the probe result.

## Debug Failure Isolation Check

Use a local test condition in which the product request can complete but the debug request returns an error or cannot be reached.

Expected results:

- Product content already returned by `/api/v1/generate-copilot` remains visible.
- The Debug Trace section displays an unavailable debug state.
- A debug request failure does not blank, overwrite or invalidate the product presentation.

## Source Probe Failure Isolation Check

Use a local test condition in which product/debug content has already rendered but the source probe request cannot be reached.

Expected results:

- The Source Probe area displays the request failure.
- Existing product content and Debug Trace remain visible.
- A source probe failure does not issue a product rerun or change product presentation.

## Boundary Checks

The frontend must observe all of the following rules:

- Product presentation always comes from `/api/v1/generate-copilot`.
- Debug state is requested only from `/api/v1/debug-copilot`.
- Source probe state is requested only from `/api/v1/debug-source-probe` while Debug Mode is enabled.
- The source probe does not execute local/mock regression anchors.
- The page must not reference `data.debug` from the product response.
- `/api/v1/generate-copilot` must not expose internal debug state.

Run this source check when the page code changes:

```powershell
rg -n "data\.debug|generate-copilot|debug-copilot|debug-source-probe|runSourceProbe|debugMode" static\index.html
```

Passing expectation:

- The output includes `generate-copilot`, `debug-copilot`, `debug-source-probe`, `runSourceProbe` and `debugMode`.
- The output contains no `data.debug` reference.

## Automated Support

The manual UI smoke protocol is complemented by fast API tests:

```powershell
.\l8\Scripts\python.exe scripts\run_all_tests.py --fast
```

The fast gate validates response contracts and live endpoint serialization with patched workflow execution; it does not replace the manual network-panel checks for the Debug Mode interaction.
