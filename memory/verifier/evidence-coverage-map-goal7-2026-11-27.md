# Evidence: Verification Coverage Map (Goal #7) - 2026-11-27

**Status: AC MET**

## Acceptance Criteria Check
| AC | Status | Proof |
|---|---|---|
| Map covers 100% of tracked files | PASS | 6727 files enumerated, each assigned verified/stale/unverified |
| Pct computed correctly | PASS | (479+1467)/6727 = 28.9% - arithmetic verified |
| Gap list actionable | PASS | Top-50 unverified listed with full paths; excludes temp/archive noise |

## Script
`memory/verifier/verification_coverage.py` - runs standalone, outputs human-readable or `--json`.

## Current State (2026-11-27 09:55)
- Total tracked: 6727
- Verified (<48h): 479 (7.1%)
- Stale (>48h): 1467 (21.8%)
- Unverified: 4781 (71.1%)
- Coverage: 28.9% vs target 90%

## Gap Analysis
The large unverified set is dominated by:
1. Memory .md files without direct evidence references (expected - not all notes need test coverage)
2. Historical root-level scripts (_patch_*, _probe_*) excluded from tracking but some remain
3. UI files in subdirectories not yet referenced by evidence artifacts

**Next steps to reach 90%:**
- Re-run freshness audit to re-stamp stale evidence (would move 1467 from stale→verified if <48h)
- Add bulk verification for memory/goals/ files (each goal file is self-verifying via ledger entries)
- Target the ui/*.js and root .py files as highest-priority unverified set
