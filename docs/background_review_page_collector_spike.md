# Background Review Page Collector Spike

## Branch

`spike/background-review-page-collector`

## Result

This spike validated that the browser extension can auto-collect visible Amazon review pages by reusing one background tab.

## Verified behavior

Manual smoke confirmed:

- Started from an already-open Amazon JP review page.
- Preserved the active review page URL as the starting point.
- Collected pageNumber 6, then pageNumber 7, then pageNumber 8.
- Used one background tab instead of opening many tabs.
- Merged collected reviews into the saved review workspace.
- Deduplicated repeated reviews across pages.
- Automatically closed the background collector tab after collection.

## Smoke result

Observed collector pages:

- Page 6: 8 visible reviews
- Page 7: 9 visible reviews
- Page 8: 9 visible reviews

Merge result:

- 17 new visible reviews
- 9 duplicate reviews skipped
- 17 total saved reviews

## Current limitation

`next_review_page_url` was empty on the tested Amazon JP pages, so the collector used the fallback pageNumber increment strategy.

That fallback worked for this test case.

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
2. Run one more smoke on a different Amazon product or review page.
3. If stable, merge the background collector into `main`.
4. Later, add a small UI control for max pages, such as 3 / 5 / 10 pages.
