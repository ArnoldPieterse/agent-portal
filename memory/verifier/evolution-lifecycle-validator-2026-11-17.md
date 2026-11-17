# Evolution full-lifecycle validator — cycle 3 (goal #10)

- timestamp: 2026-11-17T11:10:22.770342+00:00
- mode: **model** (engine in CWD: False)
- lifecycle: `propose -> test -> select -> merge -> archive`
- illegal attempts: **10** | tests 12/12 pass | all_pass=True

## Illegal transitions (must reject + keep state clean)
| case | op | before -> after | rejected | clean | error |
|---|---|---|---|---|---|
| L1_select_on_proposed | select | PROPOSED -> PROPOSED | yes | yes | select illegal: CHG-0001 is PROPOSED, not TEST_PASSED |
| L2_select_on_test_failed | select | TEST_FAILED -> TEST_FAILED | yes | yes | select illegal: CHG-0001 is TEST_FAILED, not TEST_PASSED |
| L3_merge_on_proposed | merge | PROPOSED -> PROPOSED | yes | yes | merge illegal: CHG-0001 is PROPOSED, not SELECTED |
| L4_merge_on_test_passed | merge | TEST_PASSED -> TEST_PASSED | yes | yes | merge illegal: CHG-0001 is TEST_PASSED, not SELECTED |
| L5_archive_on_selected | archive | SELECTED -> SELECTED | yes | yes | archive illegal: CHG-0001 is SELECTED, not MERGED |
| L6_archive_on_proposed | archive | PROPOSED -> PROPOSED | yes | yes | archive illegal: CHG-0001 is PROPOSED, not MERGED |
| L7_test_on_merged | test | MERGED -> MERGED | yes | yes | test illegal: CHG-0001 is MERGED, not PROPOSED |
| L8_reject_on_archived | reject | ARCHIVED -> ARCHIVED | yes | yes | reject illegal: CHG-0001 is ARCHIVED (terminal) |
| L9_select_on_rejected | select | REJECTED -> REJECTED | yes | yes | select illegal: CHG-0001 is REJECTED, not TEST_PASSED |
| L10_merge_on_archived | merge | ARCHIVED -> ARCHIVED | yes | yes | merge illegal: CHG-0001 is ARCHIVED, not SELECTED |

## Legal happy paths
| case | ops | final | expected | pass |
|---|---|---|---|---|
| H1_full_lifecycle | test->select->merge->archive | ARCHIVED | ARCHIVED | yes |
| H2_reject_from_selected | test->select->reject | REJECTED | REJECTED | yes |
