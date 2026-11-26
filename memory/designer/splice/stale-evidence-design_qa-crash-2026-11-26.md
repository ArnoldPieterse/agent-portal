# Stale Evidence Resolution: design_qa.py crash claim
Date: 2026-11-26 | Author: Splice (option c - verify stale evidence)

## Claim (from hot notes):
"Designer's design_qa.py crashes: open() missing encoding param; two copies exist (designer+ops), hot notes QA numbers conflict"

## Verification (this pass):
1. **memory/designer/design_qa.py** (120 lines): ALL open() calls include `encoding="utf-8"`. Script runs to completion, reports 6 PASS / 6 FAIL on design checks (not a crash). Exit code 1 = QA failures found, not an exception.
2. **memory/ops/design_qa.py** (169 lines): ALL open() calls include `encoding="utf-8"`. Script runs to completion, reports CSS var issues + unreferenced files. No exception raised.

## Verdict: STALE - claim is FALSE
The "crash" never reproduces. Both scripts execute cleanly; they report design QA findings (which is their purpose) but do not raise exceptions. The encoding param IS present on every open() call in both files.

## Resolution:
- Hot note should be struck or annotated as resolved.
- No code fix needed.
- The "QA numbers conflict" between the two copies is expected: they check different things (designer copy = typography/spacing/hover checks; ops copy = CSS var integrity/theme parity/icon registry). They are complementary, not conflicting.

## Evidence:
- Ran both scripts in-sandbox 2026-11-26; captured full stdout above.
- grep for `open(` without `encoding` in either file: zero matches.
