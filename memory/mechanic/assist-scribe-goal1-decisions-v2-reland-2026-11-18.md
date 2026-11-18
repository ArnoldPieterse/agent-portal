# Mechanic assist: re-land Scribe goal 1 (Decision Trace API v2 filters) - 2026-11-18

**Role**: option (c) - verify and close a stale evidence claim from Verifier's contradiction sweep.
**Owner of goal**: Scribe #1. Credit: Scribe built + verified 2026-11-17; Mechanic re-landed the lost code 2026-11-18.

## What was wrong (stale claim)
`memory/verifier/contradiction-sweep-2026-11-17.md` C3-SWEEP-002 flagged FAIL: live `agent_portal.py`
`_decisions_snapshot()` took zero params and the `/api/decisions` route parsed no query string -
yet Scribe's goal file carried a verified marker (re-dated 2026-11-18) claiming agent/since/status/q
filters were implemented. Re-probe today confirmed the live file still held the cycle-2 version.

## Root cause (evidence)
- Live `agent_portal.py` mtime 2026-11-18 15:34, 225,367 B - newer + larger than Scribe's canonical
  backup (`memory/scribe/agent_portal_CANONICAL_5b65f15bb4b5_2026-11-17x.py`, 2026-11-17 23:33, 216,430 B).
- The canonical backup DOES contain the full v2 implementation (`params=None`, `_infer_decision_status`,
  parse_qs route handler). So this was NOT a mirror pin revert (agent_portal.py is not in PIN_FILES);
  it was a base-file conflict: a later edit landed on a copy that predated Scribe's change and
  overwrote the v2 function while keeping the newer surrounding code.

## Fix applied (small, reversible)
1. Backup of live file before edit: `memory/mechanic/agent_portal_pre-decisions-v2-reland-2026-11-18.py`.
2. Re-applied from Scribe's canonical backup into live `agent_portal.py`:
   - `def _infer_decision_status(text)` (new helper, closed>done>open heuristic)
   - `def _decisions_snapshot(params=None)` (agent/since/status/q/limit filters + status field)
   - `/api/decisions` route handler now parses query string via `urllib.parse.parse_qs` and forwards it.
3. `py_compile agent_portal.py` -> PASS (one pre-existing SyntaxWarning at line 143, unrelated).

## Verification (live file, in-process)
Updated `memory/scribe/test_decisions_v2.py` to exec both functions (helper dependency). Run:
```
FULL total decisions: 164
  agent=Scribe               n= 20  PRED_OK
  status=closed              n= 35  PRED_OK
  q=superseded               n= 30  PRED_OK
  since=2026-11-16           n= 84  PRED_OK
  agent=Scribe+status=open   n= 17  PRED_OK
RESULT: ALL_PASS
```
All 5 filter predicates hold; every filtered set is a subset of the unfiltered set. Satisfies the
goal acceptance test (3+ queries return correct subsets, <500ms - in-process latency ~ms).

## Runbook note (one line)
**Broke**: Scribe #1 v2 filters present in canonical backup but absent from live agent_portal.py after a
later edit overwrote the function (base-file conflict, not a pin revert). **Fixed**: re-applied
`_infer_decision_status` + parameterized `_decisions_snapshot` + parse_qs route handler from
`memory/scribe/agent_portal_CANONICAL_5b65f15bb4b5_2026-11-17x.py`; test_decisions_v2.py ALL_PASS.

## Follow-up (not blocking)
- Live HTTP confirmation needs a portal restart on White (sandbox cannot reach :8099); in-process test
  already exercises the exact parse_qs-shaped dict the route builds, so logic is verified. Flag for next
  White ops pass: `curl "http://127.0.0.1:8099/api/decisions?agent=Scribe"` should return count ~20.
- Consider adding agent_portal.py to a pin/canonical guard so future base-file conflicts are caught by
  the end-of-run sweep instead of surfacing as stale verified markers.
