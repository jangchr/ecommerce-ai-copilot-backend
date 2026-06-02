# External Video Tool Handoff

Status: scaffold ready.

CrossGrowth generates copy-ready handoff prompts for external video tools. It does not call Gemini, Doubao, Runway, Pika, Kling, or any other external video API in this flow.

## What The Package Includes

Each product generation can include `data.external_video_tool_handoff` with:

- Gemini-style video prompt
- Doubao-style video prompt
- General image-to-video prompt
- Short motion prompt
- Scene-level keyframe prompts
- Product consistency rules
- Negative prompt
- Copy-ready generation brief
- Manual steps
- Quality checklist

## Operator Workflow

1. Generate a CrossGrowth creative brief.
2. Open the External Video Tool Handoff panel.
3. Copy the Gemini, Doubao, or general image-to-video prompt.
4. Upload or reference the product image manually in the external tool.
5. Generate one short clip first.
6. Check product consistency, evidence support, overlays, and cost.
7. Generate more clips only after quality and pricing are acceptable.
8. Paste the result URL back into the Video Job panel.

## Boundaries

- No external video API call is made by CrossGrowth.
- No cost-incurring integration is enabled.
- External tool pricing can vary.
- Real API integration requires pricing review, API key handling, explicit approval, and separate tests.
- Manual result handoff remains the source of truth.

## Public Smoke Checklist

After deployment:

1. Generate from reviews.
2. Confirm `data.external_video_tool_handoff.packet_version == external_video_tool_handoff_v1`.
3. Confirm Gemini and Doubao prompts exist.
4. Confirm keyframe prompts exist.
5. Confirm `external_api_called=false`.
6. Confirm `cost_incurred_by_crossgrowth=false`.
7. Confirm the frontend shows External Video Tool Handoff.
8. Copy Gemini prompt.
9. Copy Doubao prompt.
10. Copy full handoff package.
11. Create a Runway video job.
12. Confirm simulated provider submit/poll still works.
13. Confirm manual result handoff still works.
