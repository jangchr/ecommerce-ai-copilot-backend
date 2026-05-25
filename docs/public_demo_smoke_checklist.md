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

7. Confirm translation controls:

   - **Translate to Chinese** is visible.
   - Clicking it shows a loading state and then a Chinese Translation block.
   - **Copy Chinese Translation** works after translation succeeds.
   - Translation failure does not clear the original English result.
   - **Translate this section** is visible under Product Mode result sections.
   - **Copy section translation** works after a section translation succeeds.
   - Section translation affects only the clicked section and leaves the original English output visible.

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
   - Translation controls are usable or any translation failure is isolated from the product result.
   - Section translation controls are visible and isolated per section.

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
