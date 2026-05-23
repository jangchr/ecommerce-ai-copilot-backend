# L9 Regression Run

Generated at `2026-05-23T16:31:28`.

## Telemetry

- Total latency: 622261 ms
- Total tokens: 123890
- Estimated cost: $0.0619
- Failed nodes: None

## Cost Gate

| Metric | Actual | Warning Limit | Fail Limit | Status |
| --- | ---: | ---: | ---: | --- |
| total_tokens | 123890 |  | 135000 | PASS |
| total_latency_ms | 622261.1688162833 | 650000 | 700000 | PASS |
| storyboard_tokens | 37077 |  | 45000 | PASS |
| strategy_tokens | 24998 |  | 35000 | PASS |
| cognitive_synthesis_tokens | 27483 |  | 35000 | PASS |
| analysis_dopamine_tokens | 2559 |  | 5000 | PASS |
| failed_nodes | None |  | None | PASS |

## Diff Warnings

- phone_case: grounded_ctr dropped by 0.0103 (0.0716 -> 0.0613)

## Results

| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| balsamic_vinegar | 0.75 | 6 | 1.00 | 0.0721 | True |  | 0 | PASS |
| printer | 0.75 | 6 | 1.00 | 0.0573 | True |  | 0 | PASS |
| women_bras | 0.75 | 6 | 1.00 | 0.0633 | True |  | 0 | PASS |
| girls_overalls | 0.75 | 6 | 1.00 | 0.0567 | True |  | 0 | PASS |
| protein_powder | 0.75 | 6 | 1.00 | 0.0653 | True |  | 0 | PASS |
| phone_case | 0.75 | 6 | 1.00 | 0.0613 | True |  | 0 | PASS |
| desk_lamp | 0.75 | 6 | 1.00 | 0.0650 | True |  | 0 | PASS |
| baby_stroller | 0.75 | 6 | 1.00 | 0.0571 | True |  | 0 | PASS |
| pet_hair_vacuum | 0.75 | 6 | 1.00 | 0.0586 | True |  | 0 | PASS |
| skincare_serum | 0.75 | 6 | 1.00 | 0.0587 | True |  | 0 | PASS |

## Category Telemetry

| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balsamic_vinegar | 62258 | 12784 | 0.0064 | 10.32% | 10.01% |  |
| printer | 67396 | 13465 | 0.0067 | 10.87% | 10.83% |  |
| women_bras | 62020 | 12203 | 0.0061 | 9.85% | 9.97% |  |
| girls_overalls | 62372 | 12439 | 0.0062 | 10.04% | 10.02% |  |
| protein_powder | 60137 | 12251 | 0.0061 | 9.89% | 9.66% |  |
| phone_case | 65097 | 12566 | 0.0063 | 10.14% | 10.46% |  |
| desk_lamp | 58389 | 12096 | 0.0060 | 9.76% | 9.38% |  |
| baby_stroller | 66956 | 12210 | 0.0061 | 9.86% | 10.76% |  |
| pet_hair_vacuum | 57200 | 11581 | 0.0058 | 9.35% | 9.19% |  |
| skincare_serum | 60436 | 12295 | 0.0061 | 9.92% | 9.71% |  |
