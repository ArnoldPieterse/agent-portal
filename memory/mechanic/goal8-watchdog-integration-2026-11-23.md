# Goal #8 - Watchdog Escalation Integration (2026-11-23)

**Step taken:** Wired `EscalationChain` into `portal_watchdog.py`.

## Changes to portal_watchdog.py
- Added guarded import of `EscalationChain` (falls back gracefully if module missing).
- Replaced raw restart + immediate "NEEDS-HUMAN" with proper 3-level flow:
  - **L1**: up to 3 restart attempts with backoff [5, 15, 45]s. Recovery at any point calls `.success()`.
  - **L2**: if all L1 retries exhausted, escalation chain logs structured agent handoff request.
  - **L3**: after 45 min unresolved, chain writes NEEDS-HUMAN to `memory/ops/blockers.md`.
- Watchdog no longer short-circuits to NEEDS-HUMAN on first failed restart.

## Verification (this pass, pale sandbox)
- `py_compile memory/mechanic/portal_watchdog.py`: PASS
- `python memory/mechanic/escalation_chain.py --selftest`: **8/8 PASS**
  - L1 new incident -> level 1
  - L1->L2 after 4th fail
  - L2->L3 after 45min timeout
  - NEEDS-HUMAN written to blockers.md
  - Resolution clears state + log entries present

## Remaining for full closure
- Deploy updated `portal_watchdog.py` to White (non-sandbox seat).
- Run simulated failure: stop portal, verify L1 retries fire, confirm L2 handoff logged, confirm L3 only after timeout.
- Evidence: 3-level escalation visible in `escalation_log.jsonl` + `blockers.md`.

**Status:** Code complete + selftest green. Awaiting non-sandbox deploy for live verification.
