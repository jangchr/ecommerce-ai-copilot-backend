# Review Collector Open Tabs Spike

## Branch

`spike/review-collector-tabs`

## Result

This spike validated that the browser extension can collect visible Amazon review data from already-open tabs and merge it into one review workspace.

## Verified capabilities

- Collect visible review data from multiple already-open Amazon tabs.
- Support multiple products in the same collection run.
- Merge multiple review pages for the same product by product identity / ASIN.
- Deduplicate reviews within the same product.
- Clean common Amazon review UI noise from collected text.
- Open the merged workspace in Web Workspace.
- Analyze the merged workspace with the existing review workspace endpoint.

## Smoke result

Manual smoke confirmed a collection run with:

- 4 opened Amazon tabs.
- 3 merged products.
- 53 visible reviews after cleanup and dedupe.
- Web Workspace opened successfully.
- Workspace analysis completed successfully.

## Important boundary

The extension only collects content already visible in the user's browser tabs.

It does not:

- bypass login,
- bypass CAPTCHA,
- bypass hidden review pages,
- access content the user cannot normally see,
- handle or store user credentials.

If Amazon requires login, the user logs in normally in the browser. After the page is visible, the extension reads the visible DOM.

## Current implementation notes

Changed files:

- `browser_extension/manifest.json`
- `browser_extension/popup.js`
- `browser_extension/content.js`
- `static/index.html`
- `tests/test_browser_extension_contract.py`

Main changes:

- Added Amazon JP host permissions.
- Added product identity merge for open-tab collection.
- Added review identity dedupe.
- Added text cleanup for Amazon review UI noise.
- Added safer title cleanup for Amazon review pages.
- Fixed Web Workspace copy value syntax for `noSignalsFound`.
- Added browser extension contract tests.

## Product decision

This spike is viable.

Recommended next step:

1. Keep this branch as a successful experiment.
2. Do not merge directly until one more final smoke is completed.
3. If accepted, merge the open-tab collector enhancement into `main`.
4. Build the next spike separately for optional background single-tab multi-page collection.
