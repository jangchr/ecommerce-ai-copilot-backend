# API Examples

## Before You Begin

Start the backend from the `backend` directory:

```powershell
.\l8\Scripts\python.exe main.py
```

The examples below assume the local API is listening at:

```text
http://127.0.0.1:8001
```

The product and workflow-debug endpoints accept this request contract:

```json
{
  "url": "https://test.local/products/balsamic_vinegar",
  "goal": "tiktok_ctr",
  "real_source_mode": "local"
}
```

`goal` is optional and defaults to `tiktok_ctr`.
`real_source_mode` is optional and defaults to `local`. The only accepted values are `local` and `amazon_shadow`; `amazon_primary` is intentionally unavailable.

## Product Creative Response

### Endpoint

```http
POST /api/v1/generate-copilot
```

Use this endpoint for product-facing UI output. It returns generated creative presentation fields and intentionally does **not** return debug or internal workflow state.

### Request Body

```json
{
  "url": "https://test.local/products/balsamic_vinegar",
  "goal": "tiktok_ctr",
  "real_source_mode": "local"
}
```

Product calls should keep `real_source_mode="local"` or omit the field. The product endpoint does not return `shadow_sources`.

### curl

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/generate-copilot" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://test.local/products/balsamic_vinegar","goal":"tiktok_ctr"}'
```

### PowerShell

```powershell
$body = @{
    url = "https://test.local/products/balsamic_vinegar"
    goal = "tiktok_ctr"
    real_source_mode = "local"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/api/v1/generate-copilot" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Amazon Debug-Only Probe Example

This example probes a real Amazon product page through the debug-only surface. It is best-effort and must not be used as a product runtime dependency.

```json
{
  "product_category": "balsamic_vinegar",
  "url": "https://www.amazon.com/dp/B00QIIMCCW",
  "providers": [
    "amazon_review_api"
  ],
  "debug_only": true
}
```

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/debug-source-probe" \
  -H "Content-Type: application/json" \
  -d '{"product_category":"balsamic_vinegar","url":"https://www.amazon.com/dp/B00QIIMCCW","providers":["amazon_review_api"],"debug_only":true}'
```

```powershell
$body = @{
    product_category = "balsamic_vinegar"
    url = "https://www.amazon.com/dp/B00QIIMCCW"
    providers = @("amazon_review_api")
    debug_only = $true
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/api/v1/debug-source-probe" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

Successful Amazon probe results may include `metadata.product_title`, `metadata.rating`, `metadata.review_count`, `metadata.price`, `metadata.category_hint`, `metadata.bullet_points` and short `evidence_preview` snippets. Amazon may still return `unavailable` or `error` due to blocking, redirects, localization or DOM changes.

### Response Fields

| Field | Meaning |
| --- | --- |
| `status` | Request completion status. |
| `data.insights` | Product pain points, complaint clustering and evidence summary for presentation. |
| `data.audience` | Primary audience, sensitivity and trust barriers. |
| `data.strategy` | Product-facing creative hook and emotional trigger text. |
| `data.assets` | TikTok hook/CTA content and storyboard payload. |
| `data.evaluation` | Confidence, risk and grounded/approval status for the creative result. |
| `data.feedback` | Final user-facing feedback summary. |

The product response must not expose `data.debug`, `request_id`, `telemetry`, `telemetry_summary`, graph state, memory observability or routing internals.
Every product response carries `X-Request-ID` in the HTTP response header for correlation; observability stays out of the product JSON body.

## Debug And Regression Response

### Endpoint

```http
POST /api/v1/debug-copilot
```

Use this endpoint for regression analysis and the frontend Debug Mode trace. It exposes observability fields that are intentionally excluded from the product endpoint.

The debug response body mirrors the response header correlation ID as `request_id` and includes both node telemetry and its safe bounded aggregate, `telemetry_summary`, alongside memory health fields.

### Request Body

```json
{
  "url": "https://test.local/products/balsamic_vinegar",
  "goal": "tiktok_ctr",
  "real_source_mode": "amazon_shadow"
}
```

`amazon_shadow` is a debug-only contract mode. It is reserved for future side-channel Amazon observability and must not replace local dataset evidence, enter success memory or change product regression results.
When `real_source_mode` is `amazon_shadow`, `/api/v1/debug-copilot` may include `shadow_sources.amazon_review_api` with best-effort Amazon probe status, confidence, latency, short evidence preview and metadata. The main debug workflow result still comes from the local grounded path.

### curl

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/debug-copilot" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://test.local/products/balsamic_vinegar","goal":"tiktok_ctr"}'
```

### PowerShell

```powershell
$body = @{
    url = "https://test.local/products/balsamic_vinegar"
    goal = "tiktok_ctr"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/api/v1/debug-copilot" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Response Fields

| Field | Meaning |
| --- | --- |
| `request_id` | Request correlation identifier mirrored from the `X-Request-ID` response header. |
| `product_category` | Category inferred or selected for retrieval. |
| `evidence` | Grounding evidence payload and source confidence signals. |
| `cognitive_state` | Structured intermediate cognitive state. |
| `execution_state` | Storyboard/reflection execution state. |
| `world_metrics` | Reward, grounded quality and failure-type metrics. |
| `telemetry` | Node-level timing, token and observability data. |
| `telemetry_summary` | Safe per-request aggregate: node count, total tokens/latency, failed nodes and token/latency hotspot nodes. |
| `memory_observability` | Memory backend, capacity and FAISS/fallback health information. |
| `shadow_sources` | Debug-only side-channel source comparison payload. Empty by default; not exposed by the product endpoint. |
| `revision_count` | Number of self-repair revisions performed. |
| `regenerate_node` | Routed regeneration target, when a further repair is required. |

In particular, Debug Mode consumers may inspect:

- `evidence`
- `world_metrics`
- `telemetry`
- `telemetry_summary`
- `memory_observability`
- `revision_count`
- `regenerate_node`

## Endpoint Boundary

The product and debug endpoints are deliberately separate:

- Render end-user product output from `/api/v1/generate-copilot`.
- Use the `X-Request-ID` response header to correlate product calls without adding observability to the product body.
- Read `request_id`, `telemetry`, `telemetry_summary` and `memory_observability` only from `/api/v1/debug-copilot`.
- Do not make product consumers depend on internal debug state.

API response contracts are defined in `schemas/api_contract.py`, and smoke-tested by `tests/test_api_contract.py` and `tests/test_api_live_smoke.py`.

## Debug-Only Real Source Probe

### Endpoint

```http
POST /api/v1/debug-source-probe
```

Use this endpoint only to inspect the status of real-source adapter probes outside the default product runtime. It does not run the creative workflow and never permits a probe result to write memory.

If `providers` is omitted or empty, the endpoint probes these disabled real adapter shells:

- `amazon_review_api`
- `tiktok_trend_api`
- `reddit_review_api`

`local_review_dataset` and `tiktok_trend_mock` are regression anchors and are not executable through this probe endpoint.

### Request Body

```json
{
  "product_category": "printer",
  "url": "https://test.local/products/printer",
  "providers": [
    "amazon_review_api",
    "tiktok_trend_api",
    "reddit_review_api"
  ],
  "debug_only": true
}
```

### curl

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/debug-source-probe" \
  -H "Content-Type: application/json" \
  -d '{"product_category":"printer","url":"https://test.local/products/printer","providers":[],"debug_only":true}'
```

### PowerShell

```powershell
$body = @{
    product_category = "printer"
    url = "https://test.local/products/printer"
    providers = @()
    debug_only = $true
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8001/api/v1/debug-source-probe" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Response Fields

| Field | Meaning |
| --- | --- |
| `request_id` | Request correlation identifier mirrored from the `X-Request-ID` response header. |
| `debug_only` | Always `true`; this response is not a product runtime output. |
| `product_category` | Category used for provider probing. |
| `results` | Per-provider status, confidence, latency, preview and metadata. |
| `fallback_required` | `true` unless at least one probe succeeds with `source_confidence >= 0.70`; signals that grounded fallback evidence would still be required. |
| `telemetry` | Probe-batch totals: summed provider latency, provider count, status counts and the mirrored fallback decision. |
| `memory_write_allowed` | Always `false`; probe results must not pollute memory. |

Only `amazon_review_api` currently has a debug-only best-effort live probe implementation. Other real providers may still return `disabled` or `unavailable`. None of these probes enter the product workflow, write memory or replace the local grounded regression datasets.
