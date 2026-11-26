# Dispatch Anti-Stale Conformance Audit
Run: 2026-11-26T11:00:28.727871+00:00
SSOT ledger generated: 2026-11-26
Window: last 200 WORK passes (157 examined of 1053 total)
Conformance: 93.63% (violations=10/157)

## Result: FAIL - SSOT fresh=False, 1 stale-SSOT agent(s), 10 true stale dispatch(es)

A *stale-SSOT* finding = the dispatcher's SSOT (goal_ledger.json) reports open=0 for an agent whose LIVE goal file still has open goals. This is the root cause of stale dispatch: the dispatcher believes the agent is done and under-dispatches real work.
A *true stale dispatch* = a WORK pass for agent A at time T where every one of A's tracked goals was already reached strictly before T (open_at(T)==0): the agent was sent to work with nothing open to do.


## SSOT-vs-live drift (root cause of stale dispatch)
- orchestrator: live_open=8 ssot_open=6
- researcher: live_open=8 ssot_open=0  **STALE-SSOT**
- builder: live_open=8 ssot_open=7
- archivist: live_open=10 ssot_open=6
- scribe: live_open=7 ssot_open=4
- verifier: live_open=10 ssot_open=6
- designer: live_open=10 ssot_open=7
- mechanic: live_open=10 ssot_open=9
- outlet: live_open=10 ssot_open=9
- pixel: live_open=7 ssot_open=9
- forge: live_open=8 ssot_open=8

## Replay leg: true stale dispatches = 10
Conformance score = 93.63% (= 100 * (1 - violations/dispatches))
- {'agent': 'researcher', 'ts': '2026-11-26T00:04:03.691956+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T00:10:24.044545+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T01:53:52.073165+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T02:00:45.058639+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T03:07:08.670726+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T09:10:21.724791+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T09:17:09.620577+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T09:26:02.191134+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T09:54:18.624505+00:00', 'all_goals_reached_before_pass': True}
- {'agent': 'researcher', 'ts': '2026-11-26T10:03:36.554075+00:00', 'all_goals_reached_before_pass': True}
