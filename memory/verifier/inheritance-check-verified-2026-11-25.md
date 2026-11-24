# Cross-Cycle Inheritance Validator — VERIFIED 2026-11-25

## Summary
Built `memory/verifier/inheritance_check.py` — validates auto-generated v2 goals from the Orchestrator's inheritance engine against 3 criteria:
1. NOT in closed_topics (sig + fuzzy title match)
2. Valid verification criteria (non-empty, >20 chars, automatable reference)
3. Correct v1 reference (source file exists or goal number present, inheritance context marker)

## Self-test
- **10/10 correctly classified** (5 valid + 5 invalid)
- CWD-independent: passes from project root AND `memory/verifier/`
- Idempotent: re-runs produce same report

## Live mode
- `inherited-goals.json` is EMPTY (engine produces no v2 goals currently — archive has no scoped-down markers matching patterns)
- Validator handles empty state gracefully: reports NO_DATA, exit 0

## Invalid cases correctly rejected
| # | Title | Rejection reason |
|---|-------|-----------------|
| I1 | Orphan Remediation Sweep | title matches closed topic (sig/text match) |
| I2 | Knowledge Graph v3 | title matches closed topic |
| I3 | Some New Goal (v2) | verification criteria too short / not automatable |
| I4 | Broken Reference Goal (v2) | referenced file does not exist |
| I5 | No Inheritance Context (v2) | no inheritance context marker |

## Files
- Script: `memory/verifier/inheritance_check.py`
- Report: `memory/verifier/inheritance_report.json`
