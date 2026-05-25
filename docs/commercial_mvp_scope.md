# Commercial MVP Scope

Date: 2026-05-25

Stage: L12.0-A Commercial MVP scope planning.

Public Demo v1 reference:

```text
Tag: public-demo-v1
Runtime snapshot commit: 81aeffa
Public URL: https://ecommerce-ai-copilot-backend.onrender.com/
```

## Current Product Boundary

Public Demo v1 is stable as a guided Product Mode demo:

- Product Mode uses 10 local grounded product slugs.
- Product Mode generates a TikTok creative brief from review pain points.
- Product Mode supports Copy Hook, Copy Storyboard and Copy Full Markdown.
- Product Mode supports full Chinese translation and section-level Chinese translation.
- Product / Debug boundaries are clear.
- Amazon URLs remain Debug Mode / Amazon Shadow only.
- `amazon_primary` is not enabled.
- Product API does not expose `shadow_sources`, telemetry or `memory_observability`.

## Target Users

### 1. Amazon / Shopify / TikTok Shop Seller

Core pain:

- They need many creative angles but usually do not have a dedicated creative strategist.
- They have product reviews but struggle to translate them into strong short-video hooks.
- They often copy competitor ad formats without understanding the buyer pain behind the product.

Why they need this:

- It turns review pain points into hooks, storyboards and risk-aware creative structure.
- It can help sellers find ad angles rooted in real customer complaints instead of generic product claims.

Can Public Demo v1 serve them now?

- Partially. It demonstrates the workflow, but stable Product Mode currently only accepts 10 local slugs.
- It cannot yet ingest their own product URL or CSV as the stable product path.

Willingness to pay:

- Medium to high if the tool supports their own products and saves testing time.
- Lower while limited to demo slugs.

Priority:

- High, but only after custom product input is added.

### 2. TikTok Ad Buyer / Performance Marketer

Core pain:

- They need fresh hooks and creatives faster than their testing calendar.
- They need to diagnose why an angle might fail before spending ad budget.
- They want evidence-backed angles, not only "viral" wording.

Why they need this:

- The tool outputs hook logic, storyboard scenes and evaluation signals in one pass.
- Grounded review evidence can support more credible test hypotheses.

Can Public Demo v1 serve them now?

- Good for demo and concept validation.
- Not yet enough for production campaign management because it lacks bulk product input, campaign history and export workflows.

Willingness to pay:

- Medium. Performance marketers pay for tools that increase test velocity, but they will ask for export, history and repeatable input support.

Priority:

- Medium-high. Strong user, but likely needs workflow polish and export features first.

### 3. UGC Creator / Short Video Script Writer

Core pain:

- They need to turn product briefs into scripts quickly.
- They often receive vague brand briefs and need specific pain-driven scenes.
- They may need multilingual variants for client communication.

Why they need this:

- It produces hooks, narration, storyboard structure and Chinese translation.
- The section-level translation feature is useful for creators working across languages.

Can Public Demo v1 serve them now?

- Yes for understanding the output style and using the copied creative brief as a writing starter.
- Limited because they cannot input arbitrary client products yet.

Willingness to pay:

- Medium. Freelancers may pay for a low-cost plan if it directly saves scripting time.

Priority:

- High as a beachhead candidate, especially if positioned as a script assistant rather than a full ecommerce intelligence platform.

### 4. Small Ecommerce Brand Owner

Core pain:

- They are responsible for product, marketing and creative without a full team.
- They know customer complaints inform ads but do not have time to analyze reviews manually.
- They need content ideas that feel concrete and not agency-expensive.

Why they need this:

- It compresses review mining, creative strategy and storyboard planning into a single flow.
- Copy buttons and translation make outputs easier to reuse or delegate.

Can Public Demo v1 serve them now?

- Good as a demo and onboarding story.
- Commercial value becomes real once they can enter their own product details, CSV reviews or controlled URLs.

Willingness to pay:

- Medium-high if the price is simple and lower than hiring a strategist or agency.

Priority:

- Highest. They have urgent creative needs, simple buying criteria and a clear before/after story.

### 5. Creative Agency / Freelancer

Core pain:

- They need to pitch multiple angles quickly.
- They need to show clients why an angle is grounded in customer pain.
- They need repeatable creative briefs and localized deliverables.

Why they need this:

- It can turn review evidence into client-ready hooks, storyboards and translated briefs.
- Evidence-backed outputs can make client approvals easier.

Can Public Demo v1 serve them now?

- Strong demo value.
- Production use needs history, export, multi-product input and maybe a client-facing report format.

Willingness to pay:

- High if it supports agency workflows and repeatable exports.

Priority:

- High, especially after export/history features.

## Recommended Beachhead User

Recommended initial beachhead:

```text
Small ecommerce brand owner
```

Reasoning:

- They feel the pain most directly: "I need better ad creatives this week."
- They are less likely to require enterprise integrations at MVP stage.
- The value proposition is easy to understand: turn customer pain into TikTok creative briefs.
- They can validate whether the brief is useful without needing complex team workflows.
- They create a natural path to adjacent users: freelancers, UGC creators and small agencies serving similar brands.

Secondary beachhead:

```text
TikTok ad creative freelancer / small agency
```

This group may pay earlier if export and client-ready presentation improve, but they may also demand more workflow polish.

## MVP Value Proposition

One-line definition:

```text
Generate grounded TikTok ad hooks and storyboards from ecommerce review pain points, with one-click Chinese translation.
```

What it solves:

- The blank-page problem for ecommerce short-video creative.
- The gap between raw reviews and usable TikTok ad scenes.
- The risk of writing generic scripts that are not tied to real buyer pain.
- The bilingual handoff problem for teams or creators working in English and Chinese.

Input:

- Current stable demo: one of 10 local grounded product slugs.
- Near-term commercial path: product description, CSV reviews or controlled product/review input.

Output:

- Evidence Snapshot.
- Target Audience.
- Creative Strategy.
- Hook.
- Storyboard.
- Evaluation.
- Copy-ready Markdown.
- Full and section-level Chinese translations.

Why it is faster than hand-writing scripts:

- It bundles review analysis, angle selection, storyboard structure and quality checks into one workflow.
- Copy actions make the output immediately portable.
- Section-level translation avoids rewriting or translating the entire brief when only one section is needed.

Why grounded evidence matters:

- Customer pain gives hooks specificity.
- Evidence quotes reduce generic marketing claims.
- Grounding makes the creative angle easier to explain to clients or teammates.
- It creates a quality boundary that pure "viral hook generators" usually lack.

## MVP Feature Boundary

### Must Include For The Next MVP

- Public Product Mode polish.
- 10 stable slug demo.
- Copy Hook.
- Copy Storyboard.
- Copy Full Markdown.
- Full Chinese translation.
- Section-level Chinese translation.
- Public demo quickstart.
- Render deployment stability.

### Explicitly Not In The Next MVP

- User login.
- Payment.
- Database history.
- Amazon URL as default Product input.
- Multi-user workspace.
- Automated Amazon scraping as primary source.
- Team collaboration.

The next MVP should earn clarity before adding account, payment or collaboration complexity.

## Next Commercial MVP Features

Recommended next features, in priority order:

1. Result history / local save.
   - Users need to compare multiple briefs and return to prior outputs.

2. Export Markdown / JSON.
   - Useful for creators, freelancers and agencies.
   - Keeps implementation simple without adding accounts.

3. Better landing page.
   - Explain the audience, the stable demo inputs and the core output in less than 30 seconds.

4. Example gallery.
   - Show generated briefs for the 10 stable slugs.
   - Helps users understand output quality before waiting for generation.

5. Feedback form.
   - Capture whether users would use the brief for a real script.
   - Collect missing feature requests without building accounts.

6. More stable product categories.
   - Expand confidence in the grounded workflow.
   - Keep local dataset as regression anchor.

7. Optional CSV/product description input.
   - Strongest path toward actual commercial usage.
   - Safer than making Amazon URL the default source immediately.

8. Controlled Amazon URL beta only after separate evaluation.
   - Keep it behind debug/shadow or explicit beta gates until reliability is proven.

## Pricing Hypothesis

### Free Demo

Who it fits:

- New visitors.
- Creators evaluating output quality.
- Small sellers testing whether the tool feels useful.

Includes:

- Public demo with stable slugs.
- Limited generations.
- Copy buttons.
- Full and section translation.

Risk:

- Free demo does not prove willingness to pay.
- Users may misunderstand the 10-slug limitation unless onboarding is clear.

### Starter Monthly Plan

Candidate price:

```text
$9-$19/month
```

Who it fits:

- Small ecommerce brand owners.
- Solo operators.
- UGC creators with recurring scripting work.

Includes:

- Custom product description or CSV input.
- Saved recent results.
- Markdown export.
- Translation.
- A monthly generation limit.

Risk:

- Needs a clear input path for user-owned products.
- If outputs are not immediately usable, churn risk is high.

### Agency / Freelancer Plan

Candidate price:

```text
$39-$99/month
```

Who it fits:

- Creative agencies.
- Freelancers producing multiple client briefs.
- Performance marketers testing many angles.

Includes:

- Higher generation limits.
- Export Markdown/JSON.
- Example gallery or brief templates.
- Multi-product batch input later.
- Client-ready reports later.

Risk:

- Agencies may demand client management, brand kits or team collaboration too early.
- Scope can balloon quickly if not kept to export/history first.

## Success Metrics

MVP success should be measured by behavior, not only page views:

- Can a new user generate their first brief within 3 minutes?
- What percentage of users click Copy Hook?
- What percentage click Copy Storyboard or Copy Full Markdown?
- What percentage use full Chinese translation?
- What percentage use section-level translation?
- Does a user try a second product slug?
- Does a user say they would use the result for a real TikTok script?
- What is the most common blocker in feedback?
- How often do users try to paste Amazon URLs into Product Mode despite the boundary copy?

## Roadmap Recommendation

Suggested next sequence:

```text
L12.0-B User workflow design
L12.0-C Public landing conversion copy
L12.0-D Feedback collection flow
L12.0-E Export/history planning
L12.1 Controlled Amazon primary design
```

Principle:

Do not rush into `amazon_primary`. First prove that a specific user segment wants the output, understands the input boundary and uses the copy/translation actions.
