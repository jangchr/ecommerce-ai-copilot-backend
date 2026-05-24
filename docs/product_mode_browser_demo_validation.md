# Product Mode Browser Demo Validation

Date: 2026-05-24

Milestone: L11.0-E Product Mode browser demo validation

Target URL: `http://127.0.0.1:8001/`

## Scope

This validation used the browser UI rather than direct API calls for the main product flow. No workflow, Agent prompt/schema/reward/routing, grounded gate, cost gate, or regression threshold changes were made.

## Product Mode

Input: `balsamic_vinegar`

Debug Mode: Off

Result: PASS with one UI note.

Observed product output:

- Evidence / insights were visible.
- Audience was visible.
- Strategy was visible.
- Storyboard / assets were visible.
- Evaluation / reward fields were visible.
- Product result used `local_dataset+mock`.
- Review confidence was `0.75`.
- Evidence alignment was `1.00`.
- The run was grounded and approved.

Internal observability boundary:

- No visible `telemetry_summary` object.
- No visible `shadow_sources` object.
- No visible `memory_observability` object.
- L11.0-E UI issue: a lightweight `DEBUG TRACE` text block remained visible even when Debug Mode was off. It did not expose the structured telemetry or shadow source objects listed above.
- L11.0-F fix target: Product Mode should hide the Debug Trace panel entirely while Debug Mode is off.

Copy controls:

- `Copy Hook`: PASS, UI returned `Hook copied.`
- `Copy Storyboard`: PASS, UI returned `Storyboard copied.`
- `Copy Full Markdown`: PASS, UI returned `Full Markdown copied.`

## Debug Mode

Input: `balsamic_vinegar`

Debug Mode: On

Result: PARTIAL PASS.

Observed debug output:

- Debug Trace was visible.
- Full debug response content was visible, including telemetry and memory observability.
- Source Probe was runnable from the browser UI.
- Source Probe returned the expected disabled/unavailable real-source shell statuses for `amazon_review_api`, `tiktok_trend_api`, and `reddit_review_api`.
- Source Probe did not affect the product result display.

Source Probe observed summary:

- Provider count: `3`
- Success count: `0`
- Disabled count: `2`
- Unavailable count: `1`
- Fallback required: `true`

## Amazon Shadow

Result: BLOCKED in browser validation.

The browser automation security policy blocked the Amazon Shadow browser action before completion. I did not bypass this with direct API calls or non-browser workarounds, so this document does not claim browser-level Amazon Shadow validation.

Expected safety boundary remains covered by existing automated tests:

- Product API does not expose `shadow_sources`.
- Debug API can expose `shadow_sources`.
- `memory_write_allowed=false`.
- `used_for_generation=false`.
- Amazon shadow does not enter the default product generation path.

## Conclusion

Product Mode local demo is usable for the stable local grounded slug path with `balsamic_vinegar`. Copy controls are functional. Debug Trace and Source Probe are browser-verified. Amazon Shadow browser validation remains pending because the browser action was blocked by the automation security policy.

## L11.0-F Follow-Up

The L11.0-F cleanup hides the Debug Trace panel when Debug Mode is off and keeps Debug Trace, Source Probe and Amazon Shadow Summary available only when Debug Mode is on. Re-run the Product Mode smoke protocol to confirm the visual cleanup in a browser.
