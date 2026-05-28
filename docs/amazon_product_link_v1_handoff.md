# Amazon Product Link v1 Handoff

Status: shipped and publicly verified

Commit: 2518f8f

Feature: L26-G Amazon Product Link primary path + Generate from Amazon flow

## Final User Experience

The public demo now supports Amazon Product Link as a primary homepage entry path.

User flow:

1. Open the public demo.
2. Choose Amazon Product Link.
3. Paste an Amazon.com product detail URL.
4. Click Fetch Amazon signals.
5. Review extracted product signals.
6. Click Generate from Amazon.
7. The generated brief appears in the main result panel.
8. Recent Generations stores the new result.

Verified URL:

    https://www.amazon.com/dp/B00QIIMCCW

Verified product:

    Colavita Balsamic Vinegar - 8.5 oz

## Implemented Scope

The shipped v1 includes:

- Amazon Product Link homepage entry card.
- Dedicated Amazon product workspace.
- Amazon intake panel mounted as the primary Amazon workflow.
- Fetch Amazon signals button.
- Generate from Amazon button.
- Amazon intake result rendering.
- Reuse of the existing Product Description generation flow.
- Recent Generations compatibility.
- English and Chinese UI copy coverage.
- Frontend boundary tests for the Amazon product path.

## Important Implementation Decision

Generate from Amazon intentionally does not duplicate generation or result-rendering logic.

The final flow is:

    generateFromAmazonIntake()
    -> applyAmazonIntakeToDescriptionForm()
    -> generateFromDescription()
    -> existing product description renderer
    -> existing recent generation save path

This avoids a separate Amazon-only rendering path and keeps the main result panel behavior consistent with Product Idea generation.

## Protected Boundaries

This release does not add:

- A new /api/v1/amazon-generate endpoint.
- A separate Amazon generation backend path.
- Schema changes.
- source_adapters changes.
- Debug / Amazon Shadow behavior changes.
- A duplicate frontend result renderer.
- A database or account system.

## Validation Summary

Local validation passed:

- Browser smoke passed.
- Frontend boundary test passed: 68 tests OK.
- Fast gate passed: 204 tests OK.
- All L9 fast regression tests passed.

Public Render validation passed:

- /healthz returned ok.
- /api/v1/amazon-intake returned success.
- provider_status was success.
- fallback_required was false.
- Public HTML included Amazon Product Link markers.
- Public browser smoke passed.

Verified public markers:

- pathAmazonProductCard
- amazonProductWorkspace
- amazonIntakeGenerateBtn

## Public API Smoke Result

Public Amazon intake smoke returned:

- provider_status: success
- source_confidence: 0.85
- product_title: Colavita Balsamic Vinegar - 8.5 oz
- rating: 4.6
- review_count: 485
- fallback_required: false

## Known Non-Blocking Observation

A browser console 404 may appear for /favicon.ico.

This is not part of the Amazon Product Link workflow and is not a blocker for L26-G.

## Next Recommended Product Step

Do not add more intermediate documentation for this release.

Recommended next product work should be chosen from actual usage feedback or a clear final-product objective, for example:

- Amazon fallback UX when product signals are unavailable.
- Amazon result copy polish if real users find the generated brief unclear.
- More robust Amazon URL examples and unsupported-link guidance.
- Real user trial with Amazon Product Link as the first path.

Until then, L26-G should be treated as shipped.
## L27-A Amazon Fallback Customer Feedback Path

Status: shipped and publicly verified

Feature: Amazon Product Link fallback path for unsupported or unavailable product signals.

Final user experience:

1. User opens Amazon Product Link.
2. User pastes an unsupported or unavailable URL.
3. Fetch Amazon signals returns fallback state.
4. The page shows `Paste reviews or bullets instead`.
5. Clicking the fallback button opens Customer Feedback.
6. The pasted reviews field is prefilled with an Amazon fallback note and the original URL.
7. The user can continue with the existing Generate from customer feedback path.

Verified fallback URL:

    https://example.com/not-amazon

Verified public markers:

- amazonIntakeFallbackBtn
- useAmazonFallbackReviews
- amazonFallbackReviewsReady
- fallbackBtn.hidden = canUseAmazonSignals

Validation:

- Frontend boundary tests passed: 69 tests OK.
- Fast gate passed: 205 tests OK.
- Local browser fallback smoke passed.
- Public Render marker smoke passed.
- Public browser fallback smoke passed.
- Public Amazon success path still shows Use this info in form and Generate from Amazon.

Protected boundaries:

- No new backend endpoint.
- No Amazon generate endpoint.
- No source adapter changes.
- No Debug / Amazon Shadow behavior changes.
- No automatic fallback generation.
- No duplicate result renderer.

Product value:

This closes the main Amazon Product Link failure path. If Amazon signals are unavailable, the user is no longer blocked and can continue with customer reviews, product bullets, or buyer language.
