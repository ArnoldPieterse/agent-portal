# Evidence: Escalation Chain Selftest — Mechanic Goal 8
**Agent:** Builder (assist)
**Date:** 2026-11-22
**Goal:** memory/goals/mechanic.md #8 (Alert Escalation Chain)

## What ran
`python memory/mechanic/escalation_chain.py --selftest`

## Result
**8/8 PASS** — all 3 levels fire correctly, each level logged, NEEDS-HUMAN only after full chain exhausted.

| # | Test | Status |
|---|------|--------|
| 1 | L1 new incident -> level 1 | PASS |
| 2 | L1 second fail -> still level 1 | PASS |
| 3 | L1 third fail -> still level 1 | PASS |
| 4 | L1→L2 after 4th fail (>3 max retries) | PASS |
| 5 | L2→L3 after 45min timeout | PASS |
| 6 | NEEDS-HUMAN written to blockers.md | PASS |
| 7 | Resolution clears state | PASS |
| 8 | Log has incident_open + escalate + resolved | PASS |

## AC Coverage
- ✅ simulated failure escalates correctly through all 3 levels (tests 1-5)
- ✅ each level logged (test 8: log contains all event types)
- ✅ NEEDS-HUMAN only after full chain exhausted (test 6: written only at L3)

## Note
The doc `memory/mechanic/escalation-chain.md` also exists. The remaining AC item is "implement in watchdog" — i.e., wire the EscalationChain class into the live watchdog loop on White. That requires a non-sandbox seat with the watchdog running.
