# Public Demo v1 Archive

Date: 2026-05-25

Archive label:

```text
public-demo-v1
```

Commit:

```text
81aeffa
```

Public URL:

```text
https://ecommerce-ai-copilot-backend.onrender.com/
```

## Validation Snapshot

| Item | Status |
| --- | --- |
| Fast gate | PASS, 108 tests |
| Public `/healthz` | PASS |
| Public static frontend | PASS |
| Render `generate-copilot` | PASS |
| Product Mode input | `balsamic_vinegar` |
| Product Mode stable inputs | 10 local grounded slugs |
| Full translation | PASS |
| Section-level translation | PASS |
| Product / Debug boundary | PASS |

## Stable Product Inputs

Product Mode v1 is stable for the 10 local grounded slugs:

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

Amazon URLs remain Debug Mode / Amazon Shadow only and are not Product Mode v1 stable inputs.

## Runtime Notes

- Render port binding reads the platform-provided `PORT` and falls back to `8001` locally.
- Render public demo uses `ENABLE_HF_RUNTIME_MODELS=false` to avoid request-time Hugging Face embedding model loading.
- Product Mode uses local grounded reviews plus mock trend signals.
- Translation uses `/api/v1/translate-output` and does not run the creative workflow or write memory.

## Known Caveat

Render cold start or the first long Product request may be slow. Warm the service before public demos by visiting `/healthz`, opening `/`, and running `balsamic_vinegar` once.

## Related Records

- [L11.4 Public Demo Final Release Notes](release_notes_l11_4_public_demo_final.md)
- [Public Demo Polish Final Audit](public_demo_polish_final_audit.md)
- [Public Demo Quickstart](public_demo_quickstart.md)
- [Public Demo Smoke Checklist](public_demo_smoke_checklist.md)
