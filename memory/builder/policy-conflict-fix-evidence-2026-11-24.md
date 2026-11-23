# Policy Conflict Detector - fix + verification (2026-11-23 15:25 UTC)

Goal: Builder #9 (cycle-14). Script: memory/builder/policy_conflict.py

## Fix Applied
Root cause: same-line action regex `[;,]` did not handle the colon separator used in
"when X: then Y" format. Additionally, the trigger capture included the action portion.

Fix:
1. Changed same-line separator from `[;,]` to `[;,:]` (added colon)
2. Added trigger re-derivation: when a same-line action is found via colon/semicolon/comma,
   re-extract the trigger from the line prefix before the separator

## Verification
`python memory/builder/policy_conflict.py --selftest`: 4/4 ALL PASS
- AC1: Extracted 4 rules from synthetic fixture (2 files, 2 rules each)
- AC2: Detected 1 OOM + 1 disk conflicts (same trigger, different actions)
- AC3: Real scan found 31 rules, 1 conflict (no crash)
- AC4: False-positive rate 0% < 10% (0 FPs in 6 cases)

## Status
REACHED 2026-11-23 15:25 UTC
