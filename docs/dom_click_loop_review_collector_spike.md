# DOM Click Loop Review Collector Spike

## Branch

`spike/dom-click-loop-review-collector`

## Result

This spike tested whether Amazon review collection could be improved by clicking the visible load-more control multiple times inside the collector tab.

## Smoke result

Amazon JP product:

`B0F1T7R51T`

Start page:

Amazon JP review page 7.

Observed result:

- Page 1: 12 visible reviews.
- DOM click round 1: clicked the real `多显示 10 条评论` control.
- DOM click round 1 result: 23 unique visible reviews in the loaded state.
- DOM click round 2: no valid load-more target remained after filtering skip/main-content links.
- Fallback page: 9 visible reviews.
- Final merge result: 32 unique visible reviews, 12 duplicate reviews skipped.

## Important finding

The first DOM click is useful.

The second DOM click did not add more reviews.

After filtering false positives, the collector no longer clicked:

- `#skippedLink`
- `主要内容`
- `nav-assist-skip-to-main-content`

## Product decision

Do not merge the full DOM click loop into `main`.

Keep the current main product direction:

- single DOM click load-more,
- safe fallback,
- dedupe,
- repeated-page protection.

The loop adds complexity but does not currently increase the sample beyond the single-click path.

## Follow-up

The false-positive filter is useful and can be ported separately into main to make the single DOM click path safer.
