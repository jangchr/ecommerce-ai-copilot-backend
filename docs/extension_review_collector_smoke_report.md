# Extension Review Collector Smoke Report

## Summary

The browser extension review collector is now usable as a visible-page review intelligence workflow.

Current flow:

- Amazon / TikTok-like visible page
- Browser extension collects visible product signals and visible reviews/comments
- Extension stores products in a local workspace
- Extension analyzes saved workspace through backend API
- Extension can copy insights or workspace JSON
- Extension can open the workspace in the web app
- Web Workspace shows sample metadata and analysis results

This feature is not a full Amazon review crawler. It is a visible-page sample collector for creative intelligence.

## Verified capabilities

Chrome extension actions verified:

- Save current product
- Collect open tabs
- Analyze saved workspace
- Copy insights
- Copy workspace JSON
- Open in Web Workspace

The extension can collect:

- Amazon visible product information
- Amazon visible review samples
- TikTok-like visible comments
- Multiple open tabs into one workspace

## Real Amazon smoke

Verified with:

https://www.amazon.com/dp/B00QIIMCCW?th=1

Observed result:

- Product: Colavita Balsamic Vinegar - 8.5 oz
- ASIN: B00QIIMCCW
- Visible reviews collected after filtering: 12
- Raw review candidates detected: 98
- Source scope: visible_page_sample
- Review visibility status: visible_reviews_found

Rating distribution from the visible sample:

- 5-star: 9
- 4-star: 2
- 3-star: 0
- 2-star: 0
- 1-star: 1
- unknown: 0

The extension correctly filters low-information and duplicate review fragments such as:

- Images in this review
- Translate review to English
- There was a problem filtering reviews
- Rating-only fragments
- Title-only fragments
- Aggregate duplicate blocks

## Amazon sign-in boundary

Amazon product-reviews pages may redirect to sign-in.

The extension detects this state and surfaces:

Amazon sign-in required. The extension only collects visible page content.

The extension does not bypass login, CAPTCHA, hidden review pages, or platform restrictions.

## Web Workspace

Verified locally and on Render:

- Open in Web Workspace
- Imported review workspace appears
- Scope / rating mix / warning appears
- Analyze workspace returns Products / Reviews / High-signal
- Sample note appears above analysis results
- Top pain points and hooks are displayed

Verified sample warning:

Visible Amazon review sample only. Sorting may reflect Amazon's current page state, not the full review set.

## Product boundary

This feature should be described as:

Visible review sample collector for creative signals.

It should not be described as:

- Full Amazon review crawler
- Complete review dataset extractor
- Unbiased statistical review sampler

Supported use cases:

- Find buyer language
- Find pain points
- Find objections
- Find positive proof
- Find creative hooks
- Build ad briefs from visible comments
- Compare multiple visible product pages

Unsupported use cases:

- Full Amazon review scraping
- Bypassing Amazon login
- Bypassing CAPTCHA
- Claiming complete rating distribution
- Claiming statistical representativeness

## Current user-facing message

The extension and Web Workspace should keep this positioning clear:

Visible-page sample only. The browser extension collects content already visible in your tab and does not bypass login, CAPTCHA, hidden review pages, or platform restrictions. Use this for creative signals, not full review statistics.

## Current implementation status

Completed:

- L38-C: TikTok visible comment extraction
- L38-D: Productized extension workspace analysis display
- L38-E: Collect open tabs
- L38-F: Collected products list
- L38-G: Copy insights and workspace JSON
- L38-H: Open extension workspace in web app
- L38-I: Amazon capture diagnostics and quality filtering
- L38-J: Web Workspace sample metadata
- L38-K: Render online smoke
- L38-L: Visible sample boundary UX copy

## Recommended next steps

Next product work should focus on turning the collected review workspace into stronger creative output:

1. Improve generated ad scripts using visible review evidence.
2. Add a Web Workspace section for evidence quotes grouped by pain point.
3. Add export-ready creative brief from extension workspace.
4. Add cleaner multi-product comparison view.
5. Add optional screenshot or paste fallback for review pages that require login.

## Final status

The extension review collector is now a real usable product capability.

It solves the original friction problem:

Users no longer need to manually paste reviews one by one. They can collect visible reviews/comments from open tabs and analyze them as one workspace.

The main limitation is clear and acceptable:

It only analyzes visible page samples, not full platform review datasets.
