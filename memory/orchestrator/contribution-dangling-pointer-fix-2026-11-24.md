# Orchestrator contribution: dangling-pointer auto-triage script (2026-11-24)
Round topic: Closed-Loop Autonomy & Fleet Cockpit

## What was done
Built `memory/ops/dangling_pointer_fix.py` — a self-healing KB tool that:
1. Runs `stale_claim_check.py` to find all missing file references (50 found)
2. Categorizes them: TEMPLATE (13, YYYY-MM-DD placeholders), TEST_ARTIFACT (6, intentional test targets), REAL_DANGLING (31)
3. For REAL_DANGLING, fuzzy-matches against actual directory contents — 20 have close matches (fixable), 11 are truly lost
4. Dry-run by default; `--execute` applies fixes to source files

## Why it matters
The 50 dangling refs accumulate passively after every goal-file edit and mirror sync cycle. Without auto-triage, they degrade the Archivist's search index and confuse agents reading INDEX files. This script makes the fix a one-command step: `python memory/ops/dangling_pointer_fix.py --execute`

## Verification
- Dry-run completed cleanly (exit 0)
- Correctly identifies all 3 categories
- Fuzzy matches are reasonable (e.g., `goal5-egress-v2-closure-verified` -> `goal5-egress-v2-closure`)
- No false positives in the TEMPLATE/TEST_ARTIFACT buckets

## Artifact
- memory/ops/dangling_pointer_fix.py (new)
- memory/ops/INDEX.md (updated with pointer)
