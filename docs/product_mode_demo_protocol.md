# Product Mode Demo Protocol

## Purpose

This protocol describes the local Product Mode demo path for the grounded ecommerce creative agent backend. It keeps the stable product workflow separate from Debug Mode, Source Probe and Amazon Shadow observability.

## Start The Backend

From the `backend` directory:

```powershell
.\l8\Scripts\python.exe main.py
```

Open the local UI:

```text
http://127.0.0.1:8001/
```

FastAPI documentation remains available for API debugging:

```text
http://127.0.0.1:8001/docs
```

## Docker / Container Demo URL

When the backend runs inside the Docker image, the container should expose the same Product Mode URL on the mapped host port:

```powershell
docker run --rm --name grounded-agent-smoke -p 8001:8001 --env-file .env grounded-agent-backend
```

```text
http://127.0.0.1:8001/
```

Container smoke should also verify:

- `/` returns Product Mode HTML containing `Product Mode is stable` or `balsamic_vinegar`.
- `/static/index.html` returns HTML containing `Copy Hook`.
- These checks validate static serving only and do not run the workflow.

## Product Mode Inputs

The default Product Mode input is:

```text
balsamic_vinegar
```

Use one of the 10 local grounded slugs for stable product demos:

```text
balsamic_vinegar
printer
women_bras
girls_overalls
protein_powder
phone_case
desk_lamp
baby_stroller
pet_hair_vacuum
skincare_serum
```

Do not enter an Amazon URL in Product Mode. Amazon URLs are only for Debug Mode / Amazon Shadow checks and are not the stable product input path.

## Product Mode: Debug Mode Off

1. Turn **Debug Mode** off.
2. Enter `balsamic_vinegar` or another stable local slug.
3. Click **Run Workflow**.
4. Inspect the browser Network panel.

Expected results:

- One product request is issued: `POST /api/v1/generate-copilot`.
- No `POST /api/v1/debug-copilot` request is issued.
- No `POST /api/v1/debug-source-probe` request is issued.
- Amazon Shadow is hidden and cannot be triggered.
- The page does not display debug telemetry, memory observability or `shadow_sources`.
- The page does not display `DEBUG TRACE` or the Debug Trace panel.

Expected Product output sections:

- `insights`
- `audience`
- `strategy`
- `assets`
- `evaluation`
- `feedback`

## Debug Mode On

1. Turn **Debug Mode** on.
2. Run the workflow with a local slug.
3. Inspect the Debug Trace panel.

Expected results:

- Product output still comes from `/api/v1/generate-copilot`.
- Debug Trace is loaded from `/api/v1/debug-copilot`.
- Source Probe can be run manually through the **Run Source Probe** button.
- Amazon Shadow can be enabled for debug-only shadow observation.
- Amazon Shadow must not alter product output, write memory or enable `amazon_primary`.

## Copy Controls

After Product Mode output renders, verify:

- **Copy Hook** copies the generated hook text.
- **Copy Storyboard** copies the scene graph/storyboard text.
- **Copy Full Markdown** copies a complete Markdown package with evidence, pain points, audience, strategy, hook, storyboard, CTA, evaluation and feedback.

If browser clipboard permissions are unavailable, the UI should show a copy-unavailable status without breaking the product result.

## Demo Pass Criteria

The local demo passes when:

- A stable local slug produces grounded product output.
- Debug Mode Off does not issue debug or source-probe requests.
- Amazon URLs are clearly marked as Debug Mode / Amazon Shadow only.
- Product Mode does not show telemetry, `shadow_sources` or memory observability.
- Product Mode does not show `DEBUG TRACE`.
- Copy controls are visible and do not affect workflow execution.
