# L11.4 Public Demo Final Release Notes

Date: 2026-05-25

Scope: final public demo polish release record for the grounded ecommerce creative agent Product Mode.

## Summary

L11.4 finishes the public demo layer around the stable Product Mode backend. The release keeps the `/api/v1/generate-copilot` product contract unchanged, preserves the local grounded dataset regression anchor, and leaves Debug Mode / Amazon Shadow as diagnostic-only surfaces.

## Completed Work

- Landing copy polish: the public page now explains that this is a grounded ecommerce creative agent demo.
- Stable input guidance: the 10 local grounded slugs are visible, with `balsamic_vinegar` recommended as the first run.
- Result readability polish: Product output is organized as a user-facing TikTok creative brief.
- Full output translation: `Translate to Chinese` and `Copy Chinese Translation` are available through `/api/v1/translate-output`.
- Section-level translation: major Product sections support `Translate this section` and `Copy section translation`.
- Section translation placement fix: section translation controls now appear in the section header row, and section text is built from visible Product output rather than debug state.
- Frontend relative API path fix: public frontend requests use relative API paths instead of `127.0.0.1`.
- Render port binding hardening: the service reads Render's injected `PORT` and falls back to `8001` locally.
- Render `generate-copilot` runtime model loading hardening: `ENABLE_HF_RUNTIME_MODELS=false` avoids request-time Hugging Face embedding model loading for the public demo.

## Public Smoke Validation

Public URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

Final public demo facts:

- Public `/healthz`: PASS.
- Public static frontend `/`: PASS.
- Public `/api/v1/generate-copilot`: PASS.
- Product input: `balsamic_vinegar`.
- Public `generate-copilot` status: `200 OK`.
- Prior Render `generate-copilot` `502` / abrupt-close behavior was resolved by runtime model loading hardening.
- Translation endpoint: PASS.
- Full `Translate to Chinese`: PASS.
- Section-level `Translate this section`: PASS.
- `Copy Chinese Translation` and `Copy section translation`: PASS.
- Product Mode does not display Debug Trace, telemetry, `shadow_sources` or `memory_observability`.
- Debug Mode still retains Debug Trace, Source Probe and Amazon Shadow Summary.

## Runtime Policy

Render public demo configuration:

```dotenv
ALLOW_REAL_SOURCE_ADAPTERS=false
ENABLE_HF_RUNTIME_MODELS=false
MEMORY_MAX_RECORD_COUNT=500
```

`ENABLE_HF_RUNTIME_MODELS=false` is intentional for the public demo. Product Mode does not need request-time Hugging Face embedding model downloads or initialization to use local grounded evidence and deterministic JSON memory fallback.

## Stable Product Inputs

Product Mode remains stable for these 10 local grounded slugs:

```text
balsamic_vinegar
printer
women_bras
girls_overalls
protein_powder
phone_case
desk_lamp
baby_stroller
pet_hair_vacuum
skincare_serum
```

Amazon URLs are not Product Mode stable inputs. Amazon URLs remain Debug Mode / Amazon Shadow only.

## Known Caveats

- Render cold starts may make the first page load or first Product generation slower.
- Long Product requests can still be slower on small Render instances.
- Public demo quality is intentionally anchored to the 10 stable local grounded slugs.
- Amazon real-source data is still debug-only / shadow-only and does not enter Product generation or success memory.

## Status

```text
L11.4 public demo UX polish complete
Public Demo Done
```
