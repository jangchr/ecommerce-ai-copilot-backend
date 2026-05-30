# Background Review Page Collector Spike

## Branch

`spike/background-review-page-collector`

## Result

This spike validated that the browser extension can auto-collect visible Amazon review pages by reusing one background tab.

## Verified behavior

Manual smoke confirmed:

- The collector can start from an already-open Amazon review page.
- The collector can preserve the active review page URL as the starting point.
- The collector can move from pageNumber 6 to pageNumber 7 and pageNumber 8 on Amazon JP.
- The collector can reuse one background tab instead of opening many tabs.
- The collector can merge collected reviews into the saved review workspace.
- The collector can deduplicate repeated reviews across pages.
- The collector automatically closes the background collector tab after collection.
- The collector detects repeated visible review page content and stops early.

## Smoke result 1: Amazon JP review page

Observed collector pages:

- Page 6: 8 visible reviews
- Page 7: 9 visible reviews
- Page 8: 9 visible reviews

Merge result:

- 17 new visible reviews
- 9 duplicate reviews skipped
- 17 total saved reviews

## Smoke result 2: Amazon US repeated page content

Observed collector pages:

- Page 1: 16 visible reviews
- Page 2: repeated visible content detected

Merge result:

- 16 new visible reviews
- 0 duplicate reviews merged after early stop
- 16 total saved reviews

The collector correctly stopped early instead of pretending to collect three useful pages.

## Current limitation

`next_review_page_url` was empty on tested Amazon JP and Amazon US pages, so the collector used the fallback pageNumber increment strategy.

The fallback worked on Amazon JP for page 6 -> page 7 -> page 8.

On one Amazon US product, pageNumber 2 returned the same visible content as page 1. The collector now detects this and stops early.

## Boundary

The collector only opens and reads pages visible to the user's browser session.

It does not:

- bypass login,
- bypass CAPTCHA,
- bypass hidden review pages,
- access content the user cannot normally view,
- handle or store user credentials.

If Amazon requires login, the user logs in normally in the browser first.

## Product decision

This spike is viable.

Recommended next step:

1. Keep this branch as a successful experiment.
2. Merge into `main` after final tests pass.
3. Keep default max pages conservative.
4. Later add a small UI control for max pages, such as 3 / 5 / 10 pages.
