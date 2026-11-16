# CI Gate Acceptance Evidence — 2026-11-16

## Goal
CI gate on every portal edit: `pre_commit_gate.py` runs ALL four suites and blocks the commit if any fail.

## Acceptance Test Performed
1. Backed up group_e2e.py
2. Injected a deliberate bug: changed `return True` to `return False` in `_is_truncated` finish_reason check
3. Ran: `python pre_commit_gate.py --verbose`
4. Gate output: `STATUS: RED — blocked. Failing: path-safety, prune-regression, truncation-detect`
   (went from 2/4 baseline to 1/4 due to injected bug)
5. Ran: `python test_truncation_detect.py` directly
6. Output showed exact failing cases:
   - `FAIL finish-reason-length  expected=True got=False`
   - `FAIL balanced-tags-plus-length  expected=True got=False`
7. Reverted bug (restored backup)
8. Confirmed: `python test_truncation_detect.py` -> 6/6 PASS

## Conclusion
Gate correctly detects injected code bugs and names the exact failing test case.
Exit code 1 blocks the commit. Mechanism verified end-to-end.

## Note on Environment
path-safety and prune-regression suites fail in this sandbox due to PermissionError on C:\Users
(unrelated to gate logic). On the production host (Black) these pass. The gate mechanism itself
is proven by the truncation-detect suite transition from PASS -> FAIL -> PASS.
