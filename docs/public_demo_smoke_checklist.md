# Public Demo Smoke Checklist

Use this checklist before a public Product Mode demo.

Public URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

## Demo-Ready Checks

1. Open the public URL:

   ```text
   https://ecommerce-ai-copilot-backend.onrender.com/
   ```

2. Check health:

   ```text
   GET https://ecommerce-ai-copilot-backend.onrender.com/healthz
   ```

   Expected:

   ```text
   status = ok
   ```

3. Check the Product Mode page:

   ```text
   GET https://ecommerce-ai-copilot-backend.onrender.com/
   ```

   Expected:

   - Page loads.
   - Product Mode helper is visible.
   - `balsamic_vinegar` appears as the default or recommended input.

4. Run Product Mode:

   ```text
   input = balsamic_vinegar
   ```

   Click **Run Workflow**.

5. Confirm product result:

   - `grounded=true`
   - `approved=true`
   - Evidence / Audience / Strategy / Storyboard / Evaluation are visible.

6. Confirm copy controls:

   - **Copy Hook** works.
   - **Copy Storyboard** works.
   - **Copy Full Markdown** works.

## Render Cold Start Expectations

Render may cold start the service.

Expected symptoms:

- First page open may be slow.
- First generation may be slow.
- A temporary `502`, timeout, or connection close can happen while the instance wakes.

Recommended response:

- Wait 1-3 minutes.
- Refresh the page.
- Retry `balsamic_vinegar`.
- If failures continue, check Render service logs.

## Five-Minute Pre-Demo Warmup

Run this 5 minutes before a live demo:

1. Visit:

   ```text
   https://ecommerce-ai-copilot-backend.onrender.com/healthz
   ```

2. Visit:

   ```text
   https://ecommerce-ai-copilot-backend.onrender.com/
   ```

3. Run Product Mode once with:

   ```text
   balsamic_vinegar
   ```

4. Confirm:

   - Product output renders.
   - `grounded=true`.
   - `approved=true`.
   - Copy buttons are usable.

5. Leave the browser tab open for the demo.

## Stable Demo Inputs

Use one of the 10 stable local grounded slugs:

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

Do not use Amazon URLs in Product Mode. Amazon URLs are Debug Mode / Amazon Shadow inputs only.
