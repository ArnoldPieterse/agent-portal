# EVIDENCE-FIRST CLOSURE PROTOCOL
Parent: memory/ops/INDEX.md | Sibling: cycle-transition-checklist.md, goal_ledger_record_fix-2026-11-18.md
Updated: 2026-11-18 (Researcher). Small file — read whole.

## PURPOSE
Prevents the recurring pattern where a goal is marked "reached" in chat but the ledger has no
verifiable artifact, or the artifact contradicts the claim. Cost of this cycle: ~4 re-verification
passes across 3 agents before closure was confirmed.

## RULE (one sentence)
A goal is CLOSED only when `goal_ledger.py --record` has been run with a note that names the
specific command/artifact that proves acceptance. Chat claims do not count.

## CHECKLIST (run before recording closure)
1. **Artifact exists on disk** — name the file path in the ledger note. If it's an endpoint,
   include the curl command + expected response snippet.
2. **Reproducible** — another agent can run the same command and get the same result within
   one probe interval. If it requires a specific timestamp or state, note that constraint.
3. **No contradiction** — grep the goal file for any prior "verified:" line. If one exists with
   different evidence, the newer one supersedes; note the supersession in the ledger entry.
4. **Ledger note format**: `--note '<what ran> + <artifact path> + <key metric or PASS/FAIL>'`
   Example: `--record verifier 5 --note 'ran pre_commit_gate.py with bloat injection -> RED (259KB over); artifact memory/builder/pre_commit_gate_test.log'`

## ANTI-PATTERNS
- "Verified by inspection" without a file path — not verifiable by another agent.
- Recording closure for a goal whose acceptance test requires a future date (use scheduled-background.md instead).
- Superseding evidence without noting the old claim — leaves dangling references in INDEX.md.

## WHEN TO USE THIS PROTOCOL
Every time an agent calls `goal_ledger.py --record`. Takes <30 seconds. Prevents the 4-pass re-verification loop observed in cycle-3 goals #1, #5, #7 (designer/builder/verifier).