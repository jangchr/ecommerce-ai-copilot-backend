# DOM Click Load More A/B Smoke

## Result

DOM click load-more is worth keeping.

This A/B smoke compared the same Amazon JP review page with DOM click enabled and disabled.

## Test target

Product:

`B0F1T7R51T`

Start URL:

Amazon JP review page 7.

Max pages:

`3`

## A: DOM click enabled

Observed:

- Page 1: `pageNumber=7`, 12 visible reviews.
- DOM click: clicked Amazon's visible `多显示 10 条评论` control.
- Page 2: load-more state page, 23 visible reviews.
- Page 3: fallback `pageNumber=2`, 9 visible reviews.

Merge result:

- 32 unique visible reviews saved.
- 12 duplicate reviews skipped.

## B: DOM click disabled

Observed:

- Page 1: `pageNumber=7`, 12 visible reviews.
- Page 2: load-more href page, 9 visible reviews.

Merge result:

- 21 unique visible reviews saved.
- 0 duplicate reviews skipped.

## Conclusion

DOM click improved the same-page smoke from 21 unique reviews to 32 unique reviews.

Keep DOM click in the browser extension collector.

## Product boundary

This is still not a full Amazon crawler.

The collector only works with content available inside the user's browser session. It does not bypass:

- login,
- CAPTCHA,
- hidden pages,
- unavailable review data,
- platform restrictions.

User-facing wording should remain conservative:

`Try collecting more visible reviews`

Do not describe it as:

`Crawl all Amazon reviews`

## Next direction

The next practical improvement is sample expansion guidance:

- low-star review pages,
- verified purchase pages,
- variant review pages,
- competitor review pages,
- logged-in visible review pages.

Users can open these tabs manually, then use collect-open-tabs to merge and deduplicate the sample.
