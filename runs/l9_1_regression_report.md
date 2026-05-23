# L9.1 Local Grounded Dataset Regression Report

Generated from `runs/*.json`.

## Thresholds

| Metric | Threshold |
| --- | ---: |
| review_confidence | >= 0.70 |
| review_count | >= 5 |
| evidence_alignment | >= 0.50 |
| grounded_ctr | >= 0.04 |
| revision_count | <= 2 |

## Summary

All 10 local grounded dataset categories passed the L9.1 regression thresholds.

| Category | Product Category | Source Type | Review Conf | Trend Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Regenerate Node | Revisions | Result |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | --- |
| baby_stroller | baby_stroller | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0659 | true |  |  | 0 | PASS |
| balsamic_vinegar | food condiment | local_dataset+mock | 0.75 | 0.35 | 6 | 0.80 | 0.0627 | true |  |  | 0 | PASS |
| desk_lamp | consumer_home_product | local_dataset+mock | 0.75 | 0.35 | 6 | 0.80 | 0.0616 | true |  |  | 0 | PASS |
| girls_overalls | girls_overalls | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0646 | true |  |  | 0 | PASS |
| pet_hair_vacuum | pet hair vacuum | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0654 | true |  |  | 0 | PASS |
| phone_case | phone_case | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0502 | true |  |  | 0 | PASS |
| printer | printer | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0661 | true |  |  | 0 | PASS |
| protein_powder | health & fitness supplement | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0652 | true |  |  | 0 | PASS |
| skincare_serum | skincare_serum | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0715 | true |  |  | 0 | PASS |
| women_bras | women_bras | local_dataset+mock | 0.75 | 0.35 | 6 | 1.00 | 0.0656 | true |  |  | 0 | PASS |

## Conclusion

L9.1 local grounded dataset baseline is ready.
