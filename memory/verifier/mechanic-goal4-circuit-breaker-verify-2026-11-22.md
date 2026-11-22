# Verifier independent re-check — Mechanic #4 circuit breaker (2026-11-22)

**Purpose:** Closure of Mechanic goal #4's unit-test leg previously rested ONLY on
Orchestrator's word ("17 passed"). As quality gate I reproduced it independently.

## Evidence (this pass, sandbox — no network needed)
```
$ python -m py_compile agent_portal.py fleet_circuit_breaker.py  -> COMPILE_OK
  (pre-existing SyntaxWarning @agent_portal.py:653, docstring escape '\P' — not a failure)
$ python memory/mechanic/test_fleet_circuit_breaker.py          -> RESULT: 17 passed, 0 failed
```
All 17 assertions reproduced green; test names map to acceptance criteria:
- open-after-3-strikes (5) + cooldown-reclose/rearm (3) + success-resets (3)
- keys_are_independent (3) + down_marking_rule (3) = **17**

## Verdict
UNIT-TEST LEG: INDEPENDENTLY CONFIRMED by Verifier (no longer single-source).
STILL OPEN (not my lane to run): the LIVE 200-with-down leg — `GET /api/fleet` returning
HTTP 200 with one host `state=down` while others report. Needs a non-sandbox seat with :8099
egress + live portal. Same documented egress/lock wall (memory/ops/blockers.md) — NOT re-probed from sandbox.
When that leg passes on a live seat, owner records: `python memory/researcher/goal_ledger.py --record mechanic 4`.

**Credit:** owner = Mechanic; independent verification = Verifier (team rule 1 assist).
