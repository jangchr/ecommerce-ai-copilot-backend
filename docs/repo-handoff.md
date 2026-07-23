# CrossGrowth Repo Handoff

Current state: **MVP Preview Freeze complete**.

This repo is ready for first-stage handoff as a deterministic preview system. It demonstrates the CrossGrowth claim-safe ecommerce creative workflow without enabling production execution, real providers, real persistence, or real platform upload.

## Main Entry Points

- [README](../README.md)
- [MVP Preview Freeze](mvp-preview-freeze.md)
- [Post-MVP Unlock Plan](post-mvp-unlock-plan.md)
- [Demo Guide](demo-guide.md)

## Commit Baseline

- MVP freeze baseline: `a508fbb21330b350adaaeb681c0902194d3230c1`
- MVP freeze docs handoff: `450b6c1d638d2f1c6ac8c3cae1105ca0d76e2932`

## Final Verification Results

- batch-gate: 626 tests, 1 skipped, PASS
- review workspace unittest: 83 tests, PASS
- frontend probe unittest: 509 tests, 1 skipped, PASS
- agent runs unittest: 105 tests, PASS
- py_compile: PASS
- EN/ZH browser validation: PASS from the 96B browser verification
- git status at final freeze closeout: clean, `main...origin/main`

## Demonstration Path

Use the Workspace preview to walk through:

- MVP home
- scenario presets
- demo walkthrough
- evidence
- claim safety
- creative output
- delivery QA
- remediation
- final export packet
- campaign dossier
- final system health
- MVP readiness dossier

## What Not To Claim

- Do not claim a real platform pass rate.
- Do not claim a real compliance conclusion.
- Do not claim that a real ad has been generated or published.
- Do not claim that a real provider has been integrated.
- Do not claim that real customer data has been processed.
- Do not claim that real media has been uploaded, downloaded, or stored.
- Do not claim that real files have been exported or written.
- Do not claim that a real release tag, production job, or platform launch has happened.

## Disabled Capabilities

These remain disabled in the MVP Preview Freeze:

- real LLM
- provider
- media
- external scraping
- database persistence
- real execution
- real policy check
- platform upload
- task creation
- real export
- file write
- secret read
- external call
- token issue

## Phase 2 Starting Points

Future unlock work starts with explicit gates for:

- real LLM provider gate
- real database gate
- real file export gate
- platform upload gate
- task / approval gate
- audit / monitoring gate

Each gate must start from the [Post-MVP Unlock Plan](post-mvp-unlock-plan.md) and prove tests, approvals, audit controls, cost and quota guards, and rollback / failure handling before any real capability is enabled.
