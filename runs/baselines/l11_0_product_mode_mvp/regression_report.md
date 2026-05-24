# L9 Regression Run

Generated at `2026-05-24T21:22:22`.

## Telemetry

- Total latency: 540596 ms
- Total tokens: 123942
- Estimated cost: $0.0620
- Failed nodes: None

## Cost Gate

| Metric | Actual | Warning Limit | Fail Limit | Status |
| --- | ---: | ---: | ---: | --- |
| total_tokens | 123942 |  | 135000 | PASS |
| total_latency_ms | 540595.5240505682 | 650000 | 700000 | PASS |
| storyboard_tokens | 34802 |  | 45000 | PASS |
| strategy_tokens | 27387 |  | 35000 | PASS |
| cognitive_synthesis_tokens | 27919 |  | 35000 | PASS |
| analysis_dopamine_tokens | 2571 |  | 5000 | PASS |
| failed_nodes | None |  | None | PASS |

## Diff Warnings

- phone_case: grounded_ctr dropped by 0.0153 (0.0716 -> 0.0563)

## Results

| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| balsamic_vinegar | 0.75 | 6 | 1.00 | 0.0648 | True |  | 0 | PASS |
| printer | 0.75 | 6 | 1.00 | 0.0625 | True |  | 0 | PASS |
| women_bras | 0.75 | 6 | 1.00 | 0.0569 | True |  | 0 | PASS |
| girls_overalls | 0.75 | 6 | 1.00 | 0.0565 | True |  | 0 | PASS |
| protein_powder | 0.75 | 6 | 1.00 | 0.0579 | True |  | 0 | PASS |
| phone_case | 0.75 | 6 | 1.00 | 0.0563 | True |  | 0 | PASS |
| desk_lamp | 0.75 | 6 | 1.00 | 0.0648 | True |  | 0 | PASS |
| baby_stroller | 0.75 | 6 | 1.00 | 0.0562 | True |  | 0 | PASS |
| pet_hair_vacuum | 0.75 | 6 | 1.00 | 0.0577 | True |  | 0 | PASS |
| skincare_serum | 0.75 | 6 | 1.00 | 0.0635 | True |  | 0 | PASS |

## Category Telemetry

| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| balsamic_vinegar | 48473 | 11756 | 0.0059 | 9.49% | 8.97% |  |
| printer | 46344 | 11332 | 0.0057 | 9.14% | 8.57% |  |
| women_bras | 58290 | 12328 | 0.0062 | 9.95% | 10.78% |  |
| girls_overalls | 58225 | 12780 | 0.0064 | 10.31% | 10.77% |  |
| protein_powder | 55213 | 12988 | 0.0065 | 10.48% | 10.21% |  |
| phone_case | 60036 | 13260 | 0.0066 | 10.70% | 11.11% |  |
| desk_lamp | 50117 | 12182 | 0.0061 | 9.83% | 9.27% |  |
| baby_stroller | 58363 | 12964 | 0.0065 | 10.46% | 10.80% |  |
| pet_hair_vacuum | 50595 | 12139 | 0.0061 | 9.79% | 9.36% |  |
| skincare_serum | 54941 | 12213 | 0.0061 | 9.85% | 10.16% |  |
