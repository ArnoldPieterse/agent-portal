# Goal #1: First Real Canary Deploy — EVIDENCE

Date: 2026-11-17
Status: PASS

## What was done
- Cleared stale canary host copies (red/black/pale)
- Created a real portal change: `BUILD_VERSION = "3.1.0-canary"` constant added to agent_portal.py
  - Purpose: version stamp for build traceability (supports goal #10 build registry)
  - Non-critical, additive-only change
- Ran: `python memory/builder/canary_deploy.py memory/builder/canary_real_patch.diff`

## Timeline
| Phase | Timestamp (UTC) | Result |
|-------|-----------------|--------|
| Red/apply | 2026-11-17T10:21:55Z | OK |
| Red/smoke (py_compile) | 2026-11-17T10:21:55Z | syntax OK |
| Black/promote + smoke | 2026-11-17T10:21:55Z | OK |
| Pale/promote + smoke | 2026-11-17T10:21:55Z | OK |

## Rollback trigger
None fired. All hosts green on first pass.

## Artifacts
- Patch: memory/builder/canary_real_patch.diff
- Events log entry: memory/ops/canary-events.jsonl (last line, ts=2026-11-17T10:21:55Z)
- Deployed files: memory/builder/canary/red/, black/, pale/ agent_portal.py

## Note
First attempt failed (stale host copies from 2026-11-16 test runs, line mismatch).
Cleared copies, re-ran successfully. This is expected behavior - the pipeline correctly
rejected a patch that didn't match the target file state.
