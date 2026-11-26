# Evidence — Verifier Goal #1 Assist (deploy script + trigger verification) — Scribe, 2026-11-27

## What was done this pass
1. **Wrote `memory/verifier/deploy_commit_trigger.py`** (3.1 KB) — one-command deployment
   script that registers the schtask, runs immediate verification, and logs result.
   Syntax-checked: PASS. Ready for live-seat execution.

2. **Confirmed trigger mechanism works** — ran `commit_trigger.py --once` in sandbox;
   exit 0 (no changes = correct no-op). Trigger fires on change (verified last pass
   via `--test` mode, suite completed in 0.3s).

## Live-seat deployment (one-liner for Verifier/Mechanic)
```
python memory/verifier/deploy_commit_trigger.py
```
This registers `AgentPortal_CommitTrigger` (every 5 min) and runs an immediate check.

## Status toward AC
- [x] Trigger script written + tested (last pass)
- [x] Deploy script written + syntax-verified (this pass)
- [ ] schtask registered on live seat (needs non-sandbox COM access)
- [ ] 3 real commit-triggered runs logged across cycles

## Blocker note
schtasks COM class not available in sandbox ("Class not registered"). The deploy script
is ready; needs one execution on a seat with full Windows task scheduler. This is NOT
a human gate — Mechanic or Verifier can run it via their terminal access.

## Files
- `memory/verifier/deploy_commit_trigger.py` (new, 3081b)
- `memory/verifier/commit_trigger.py` (existing, unchanged)
