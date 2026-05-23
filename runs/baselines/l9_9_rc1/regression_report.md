# L9 Regression Run

Generated at `2026-05-23T18:08:48`.

## Telemetry

- Total latency: 594954 ms
- Total tokens: 128264
- Estimated cost: $0.0641
- Failed nodes: None

## Cost Gate

| Metric | Actual | Warning Limit | Fail Limit | Status |
| --- | ---: | ---: | ---: | --- |
| total_tokens | 128264 |  | 135000 | PASS |
| total_latency_ms | 594953.6123863291 | 650000 | 700000 | PASS |
| storyboard_tokens | 34629 |  | 45000 | PASS |
| strategy_tokens | 25717 |  | 35000 | PASS |
| cognitive_synthesis_tokens | 28329 |  | 35000 | PASS |
| analysis_dopamine_tokens | 2578 |  | 5000 | PASS |
| failed_nodes | None |  | None | PASS |

## Diff Warnings

- printer: grounded_ctr dropped by 0.0100 (0.0649 -> 0.0548)
- girls_overalls: grounded_ctr dropped by 0.0110 (0.0629 -> 0.0519)
- skincare_serum: grounded_ctr dropped by 0.0109 (0.0614 -> 0.0504)

## Results

| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| balsamic_vinegar | 0.75 | 6 | 1.00 | 0.0572 | True |  | 0 | PASS |
| printer | 0.75 | 6 | 1.00 | 0.0548 | True |  | 0 | PASS |
| women_bras | 0.75 | 6 | 1.00 | 0.0581 | True |  | 1 | PASS |
| girls_overalls | 0.75 | 6 | 1.00 | 0.0519 | True |  | 0 | PASS |
| protein_powder | 0.75 | 6 | 1.00 | 0.0564 | True |  | 0 | PASS |
| phone_case | 0.75 | 6 | 1.00 | 0.0644 | True |  | 0 | PASS |
| desk_lamp | 0.75 | 6 | 1.00 | 0.0622 | True |  | 0 | PASS |
| baby_stroller | 0.75 | 6 | 1.00 | 0.0614 | True |  | 0 | PASS |
| pet_hair_vacuum | 0.75 | 6 | 1.00 | 0.0596 | True |  | 0 | PASS |
| skincare_serum | 0.75 | 6 | 1.00 | 0.0504 | True |  | 0 | PASS |

## Category Telemetry

| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balsamic_vinegar | 59237 | 12412 | 0.0062 | 9.68% | 9.96% |  |
| printer | 64443 | 12684 | 0.0063 | 9.89% | 10.83% |  |
| women_bras | 83138 | 17683 | 0.0088 | 13.79% | 13.97% |  |
| girls_overalls | 57462 | 12043 | 0.0060 | 9.39% | 9.66% |  |
| protein_powder | 47662 | 11382 | 0.0057 | 8.87% | 8.01% |  |
| phone_case | 54590 | 12148 | 0.0061 | 9.47% | 9.18% |  |
| desk_lamp | 61341 | 13148 | 0.0066 | 10.25% | 10.31% |  |
| baby_stroller | 53811 | 12165 | 0.0061 | 9.48% | 9.04% |  |
| pet_hair_vacuum | 55741 | 12063 | 0.0060 | 9.40% | 9.37% |  |
| skincare_serum | 57529 | 12536 | 0.0063 | 9.77% | 9.67% |  |
