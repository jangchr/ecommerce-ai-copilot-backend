# L9 Regression Run

Generated at `2026-05-23T22:45:26`.

## Telemetry

- Total latency: 589536 ms
- Total tokens: 122386
- Estimated cost: $0.0612
- Failed nodes: None

## Cost Gate

| Metric | Actual | Warning Limit | Fail Limit | Status |
| --- | ---: | ---: | ---: | --- |
| total_tokens | 122386 |  | 135000 | PASS |
| total_latency_ms | 589536.1216870733 | 650000 | 700000 | PASS |
| storyboard_tokens | 34164 |  | 45000 | PASS |
| strategy_tokens | 26303 |  | 35000 | PASS |
| cognitive_synthesis_tokens | 27176 |  | 35000 | PASS |
| analysis_dopamine_tokens | 2575 |  | 5000 | PASS |
| failed_nodes | None |  | None | PASS |

## Diff Warnings

- pet_hair_vacuum: grounded_ctr dropped by 0.0158 (0.0636 -> 0.0477)

## Results

| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| balsamic_vinegar | 0.75 | 6 | 1.00 | 0.0564 | True |  | 0 | PASS |
| printer | 0.75 | 6 | 1.00 | 0.0567 | True |  | 0 | PASS |
| women_bras | 0.75 | 6 | 1.00 | 0.0631 | True |  | 0 | PASS |
| girls_overalls | 0.75 | 6 | 1.00 | 0.0642 | True |  | 0 | PASS |
| protein_powder | 0.75 | 6 | 1.00 | 0.0614 | True |  | 0 | PASS |
| phone_case | 0.75 | 6 | 1.00 | 0.0652 | True |  | 0 | PASS |
| desk_lamp | 0.75 | 6 | 1.00 | 0.0616 | True |  | 0 | PASS |
| baby_stroller | 0.75 | 6 | 1.00 | 0.0555 | True |  | 0 | PASS |
| pet_hair_vacuum | 0.75 | 6 | 1.00 | 0.0477 | True |  | 0 | PASS |
| skincare_serum | 0.75 | 6 | 1.00 | 0.0580 | True |  | 0 | PASS |

## Category Telemetry

| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balsamic_vinegar | 53376 | 11463 | 0.0057 | 9.37% | 9.05% |  |
| printer | 62022 | 12332 | 0.0062 | 10.08% | 10.52% |  |
| women_bras | 58132 | 11802 | 0.0059 | 9.64% | 9.86% |  |
| girls_overalls | 62429 | 12487 | 0.0062 | 10.20% | 10.59% |  |
| protein_powder | 56009 | 12196 | 0.0061 | 9.97% | 9.50% |  |
| phone_case | 66024 | 12813 | 0.0064 | 10.47% | 11.20% |  |
| desk_lamp | 57698 | 12039 | 0.0060 | 9.84% | 9.79% |  |
| baby_stroller | 64833 | 13267 | 0.0066 | 10.84% | 11.00% |  |
| pet_hair_vacuum | 55792 | 12517 | 0.0063 | 10.23% | 9.46% |  |
| skincare_serum | 53222 | 11470 | 0.0057 | 9.37% | 9.03% |  |
