# Policy Conflict Detector - evidence (2026-11-23 14:46 UTC)

Goal: Builder #9 (cycle-10). Script: memory/builder/policy_conflict.py

## Verification run (this pass)
`python memory/builder/policy_conflict.py --selftest`:
- [PASS] AC1: Extracted 4 rules from synthetic fixture
- [PASS] AC2: Detected 1 OOM + 1 disk conflicts
- [PASS] AC3: Real scan found 19 rules, 0 conflicts (no crash)
- [PASS] AC4: False-positive rate 0% < 10% (0 FPs in 6 cases)
SELFTEST: 4/4 ALL PASS

`python memory/builder/policy_conflict.py --scan`: 19 rules extracted from real policy files; report written to memory/ops/policy-conflict-report.json (schema includes rule_a/rule_b/file_a/file_b/trigger_overlap/action_divergence/severity).

## Root cause of prior selftest failure
Fixture lines use 'when X: then Y' (colon + keyword). Old code: trigger regex greedily captured the whole tail including 'then Y'; same-line action regex only handled ','/';', not ':'. Fix: marker-split pass on then/do before fallback trigger-pattern matching; head stripped of trailing punctuation and re-matched against trigger keyword.

## Status
REACHED 2026-11-23 14:46 UTC
