# Extension bilingual workspace smoke report

## Scope

This smoke report records the current validated state after:

- Commit: `ed59cc6 Localize extension workspace copy experience`
- Feature area: browser extension review collector + Web Workspace extension panel
- Validation type: manual smoke + fast regression

## Completed capability

### Browser extension popup

- The popup supports English and Chinese language switching.
- Popup UI copy is routed through a language copy map instead of hard-coded single-language strings.
- Workspace requests include `output_language` based on the selected popup language.
- Chinese mode sends `output_language: zh-CN`.
- English mode sends `output_language: en`.
- Popup analysis section localizes controlled theme labels such as:
  - price / value concern
  - taste / flavor concern
  - size / quantity mismatch
  - quantity / size uncertainty
- Original buyer review evidence remains in the original review language.

### Web Workspace extension panel

- The extension workspace panel can read the browser extension payload.
- The panel renders imported product and visible review counts.
- The panel displays the visible-page sample boundary.
- The panel supports English and Chinese UI copy.
- The panel can analyze the imported workspace.
- Creative brief output is shown inside the Web Workspace panel.

### Copy actions

Validated copy actions:

- Copy JSON
- Copy all brief
- Copy row
- Copy positive proof

Expected behavior:

- Each copy action gives visible feedback.
- Copy row feedback appears near the relevant row.
- Copy positive proof feedback appears near the positive proof button.
- Copied Markdown includes product/source/review-count/sample-warning context.

## Sample boundary

The browser extension only collects content already visible in the current tab.

It does not bypass:

- Login
- CAPTCHA
- Hidden review pages
- Platform restrictions
- Amazon review access limits

The imported review sample should be treated as a visible-page creative signal sample, not as a complete review database or full statistical sample.

## Validated workflow

Manual workflow validated:

1. Open Amazon product page.
2. Use the browser extension to save visible product/review signals.
3. Switch popup language between English and Chinese.
4. Analyze saved workspace in the popup.
5. Open the imported payload in Web Workspace.
6. Confirm the Web Workspace extension panel renders.
7. Analyze workspace.
8. Confirm Creative brief renders.
9. Use copy actions and confirm feedback appears.

## Regression status

The latest validation passed:

- `tests.test_browser_extension_contract`
- `tests.test_frontend_probe_boundary`
- `scripts/run_all_tests.py --fast`

Fast regression output included:

```text
All L9 fast regression tests passed.
Current product interpretation

The current review collector should be understood as:

A visible review signal collector
A buyer-language extractor
A creative brief generator
A bilingual extension/workspace workflow

It should not be positioned as:

A full Amazon review scraper
A complete review statistics tool
A replacement for full marketplace research
Next recommended batch

Next batch:

L40-L41A: Sample interpretation and first script pack

Recommended scope:

Add sample interpretation.
Explain what the visible sample can and cannot support.
Add strongest creative signals.
Add recommended next creative directions.
Generate first 15-second and 30-second video scripts from the sample interpretation and Creative brief.
Keep all new visible copy behind language/i18n interfaces.
