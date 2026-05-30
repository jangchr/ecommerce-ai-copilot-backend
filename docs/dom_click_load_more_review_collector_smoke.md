# DOM Click Load More Review Collector Smoke

## Result

The DOM click load-more collector improved Amazon JP visible review collection in a real smoke test.

## Verified behavior

The extension can:

- Start from an already-open Amazon review page.
- Detect Amazon's visible "多显示 10 条评论" control.
- Click the load-more control inside the collector tab.
- Wait for the loaded review state.
- Extract the expanded visible review set.
- Continue with safe fallback when useful.
- Merge and deduplicate collected reviews.
- Stop without user-visible errors.

## Smoke case

Product:

`B0F1T7R51T`

Start page:

Amazon JP review page 7.

Observed collector pages:

- Page 1: `pageNumber=7`, 12 visible reviews.
- DOM click: clicked `cm_cr_arp_d_paging_btm_2`.
- Page 2: load-more state page, 23 visible reviews.
- Page 3: fallback `pageNumber=2`, 9 visible reviews.

Merge result:

- 32 unique visible reviews saved.
- 12 duplicate reviews skipped.
- 0 failures.

## Product interpretation

This is not a full Amazon crawler.

It remains a visible-page collector that operates inside the user's browser session.

It does not bypass:

- login,
- CAPTCHA,
- hidden pages,
- platform restrictions,
- unavailable review data.

However, the DOM click path is now useful because it can trigger a richer loaded-review state than simple URL guessing in some Amazon JP cases.

## Product decision

Merge the DOM click load-more collector into `main`.

Keep the user-facing positioning conservative:

- "Try collecting more visible reviews"
- not "crawl all Amazon reviews"

## Next direction

The next practical improvement is multi-tab sample expansion guidance:

- low-star review pages,
- verified purchase pages,
- variant review pages,
- competitor review pages,
- logged-in visible review pages.
