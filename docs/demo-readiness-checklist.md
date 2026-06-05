# Demo Readiness Checklist

Status: ready for Public Demo v1 multi-agent walkthrough.

## Fixed Demo Sample

Use the `Use Multi-Agent Demo Sample` button in Customer Feedback.

- Product name: Portable Mini Blender
- Product category: kitchen_appliance
- Product description: A compact rechargeable blender for smoothies, travel, and quick morning drinks.
- Reviews:
  - Hard to clean after one smoothie.
  - Too loud for early mornings.
  - Small enough for travel but the cup sometimes leaks in my bag.
  - Blends soft fruit well, but ice takes longer.
  - Great for office smoothies when it is fully charged.
- Target platform: TikTok
- Goal: tiktok_ctr
- Output language: en

## Exact Demo Path

1. Open the public demo.
2. Choose Customer Feedback.
3. Click `Use Multi-Agent Demo Sample`.
4. Click `Generate from customer feedback`.
5. Open `Business-grounded Multi-Agent Workflow`.
6. Show Evidence Agent, Asset Lock Agent, and Keyframe Agent.
7. Open `External Video Tool Handoff`.
8. Show Product Asset Lock and Keyframe Plan.
9. Create a Video Job.
10. Submit and poll the simulated provider flow.
11. Optionally record an External Video Experiment.

## Two-Minute Demo

- Generate from the fixed sample.
- Show the multi-agent panel and explain that each agent has a goal, inputs, outputs, decisions, warnings, and business impact.
- Open External Video Tool Handoff and show Product Asset Lock plus Keyframe Plan.
- Emphasize that no external video API is called.

## Five-Minute Demo

- Run the fixed sample.
- Walk through Evidence Agent, Strategy Agent, Storyboard Agent, Asset Lock Agent, and Keyframe Agent.
- Copy the full external video handoff package.
- Create a Video Job.
- Submit and poll the simulated provider lifecycle.
- Record an External Video Experiment result URL.

## Agent vs Automation

This is not a plain automation wrapper. The workflow exposes business artifacts and handoffs:

- Evidence Agent grounds the creative in buyer language.
- Asset Lock Agent protects product identity for video generation.
- Keyframe Agent turns scenes into controllable video targets.
- Prompt Handoff Agent prepares copy-ready prompts for manual external tools.
- Cost, Provider Job, and Experiment Agents keep paid generation and manual tests trackable.

## Cost and API Safety

- CrossGrowth does not call Gemini, Doubao, Runway, Pika, or other external video APIs in this flow.
- No video provider API key is required for the demo.
- Simulated provider submit/poll is for lifecycle validation only.
- Manual result handoff remains available.

## Do Not Demo Yet

- Do not claim automated real video generation is enabled.
- Do not claim real provider pricing is final.
- Do not enter private API keys.
- Do not present Amazon URL input as full review scraping.
- Do not claim Product Asset Lock guarantees perfect visual identity; it is a control artifact for human review.
