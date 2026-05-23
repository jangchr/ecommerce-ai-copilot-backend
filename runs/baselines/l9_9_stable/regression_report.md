# L9 Regression Run

Generated at `2026-05-23T18:26:33`.

## Telemetry

- Total latency: 542513 ms
- Total tokens: 123517
- Estimated cost: $0.0618
- Failed nodes: None

## Cost Gate

| Metric | Actual | Warning Limit | Fail Limit | Status |
| --- | ---: | ---: | ---: | --- |
| total_tokens | 123517 |  | 135000 | PASS |
| total_latency_ms | 542513.4978550705 | 650000 | 700000 | PASS |
| storyboard_tokens | 34368 |  | 45000 | PASS |
| strategy_tokens | 27527 |  | 35000 | PASS |
| cognitive_synthesis_tokens | 28178 |  | 35000 | PASS |
| analysis_dopamine_tokens | 2583 |  | 5000 | PASS |
| failed_nodes | None |  | None | PASS |

## Diff Warnings

- phone_case: grounded_ctr dropped by 0.0171 (0.0716 -> 0.0545)

## Results

| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| balsamic_vinegar | 0.75 | 6 | 1.00 | 0.0617 | True |  | 0 | PASS |
| printer | 0.75 | 6 | 1.00 | 0.0558 | True |  | 0 | PASS |
| women_bras | 0.75 | 6 | 1.00 | 0.0653 | True |  | 0 | PASS |
| girls_overalls | 0.75 | 6 | 1.00 | 0.0631 | True |  | 0 | PASS |
| protein_powder | 0.75 | 6 | 1.00 | 0.0550 | True |  | 0 | PASS |
| phone_case | 0.75 | 6 | 1.00 | 0.0545 | True |  | 0 | PASS |
| desk_lamp | 0.75 | 6 | 1.00 | 0.0725 | True |  | 0 | PASS |
| baby_stroller | 0.75 | 6 | 1.00 | 0.0567 | True |  | 0 | PASS |
| pet_hair_vacuum | 0.75 | 6 | 1.00 | 0.0617 | True |  | 0 | PASS |
| skincare_serum | 0.75 | 6 | 1.00 | 0.0629 | True |  | 0 | PASS |

## Category Telemetry

| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balsamic_vinegar | 46844 | 11580 | 0.0058 | 9.38% | 8.63% |  |
| printer | 54683 | 12074 | 0.0060 | 9.78% | 10.08% |  |
| women_bras | 62379 | 13383 | 0.0067 | 10.83% | 11.50% |  |
| girls_overalls | 52897 | 11927 | 0.0060 | 9.66% | 9.75% |  |
| protein_powder | 48201 | 11332 | 0.0057 | 9.17% | 8.88% |  |
| phone_case | 52669 | 12056 | 0.0060 | 9.76% | 9.71% |  |
| desk_lamp | 56945 | 13070 | 0.0065 | 10.58% | 10.50% |  |
| baby_stroller | 54816 | 12488 | 0.0062 | 10.11% | 10.10% |  |
| pet_hair_vacuum | 55768 | 12719 | 0.0064 | 10.30% | 10.28% |  |
| skincare_serum | 57310 | 12888 | 0.0064 | 10.43% | 10.56% |  |
