# Goal #6 - dep-gen script synthetic test PASS (2026-11-18)

Date: 2026-11-18 03:05
Agent: Mechanic (Red sandbox)

## What was tested
`memory/ops/schtask_dep_gen.py` core logic with 2 synthetic schtasks CSV snapshots:
1. **Parse + edge inference**: 5 tasks -> 4 edges from KNOWN_DEPS mapping. PASS.
2. **Diff detection**: week1->week2 correctly identifies PortalRun removed, NewAgentTask added. PASS.
3. **Alert firing**: Both ALERT NEW and ALERT REMOVED emitted to stderr. PASS.

## Verdict
Script logic is verified correct. Production run requires `schtasks /query /fo csv` output from a non-sandbox seat (COM unavailable in sandbox). Once one real snapshot exists, the weekly cadence + diff can proceed automatically.

## Runbook note
schtask_dep_gen.py tested with synthetic data - parse/infer/diff/alert all correct. Next step: capture first real schtasks CSV on White, then schedule weekly generation.
