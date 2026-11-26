# Dispatch Anti-Stale Conformance Audit
Run: 2026-11-26T10:33:33.212410+00:00
SSOT ledger generated: 2026-11-26
Window: last 200 WORK passes (200 examined of 1041 total)

## Result: FAIL - SSOT fresh=False, 1 stale-SSOT agent(s), 0 true stale dispatch(es)

A *stale-SSOT* finding = the dispatcher's SSOT (goal_ledger.json) reports open=0 for an agent whose LIVE goal file still has open goals. This is the root cause of stale dispatch: the dispatcher believes the agent is done and under-dispatches real work.
A *true stale dispatch* = a WORK pass where even the live file shows no open goals (by-design idle-contribution regime is NOT counted).


## SSOT-vs-live drift (root cause of stale dispatch)
- orchestrator: live_open=8 ssot_open=6
- researcher: live_open=8 ssot_open=0  **STALE-SSOT**
- builder: live_open=9 ssot_open=7
- archivist: live_open=10 ssot_open=6
- scribe: live_open=7 ssot_open=4
- verifier: live_open=10 ssot_open=6
- designer: live_open=10 ssot_open=7
- mechanic: live_open=10 ssot_open=9
- outlet: live_open=10 ssot_open=9
- pixel: live_open=10 ssot_open=9
- forge: live_open=8 ssot_open=8

## Replay: idle-contribution passes (by-design fallback): 0
True stale dispatches (replay leg): 0
