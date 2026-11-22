# Live-Leg Runbook Pre-Flight Check
Author: Mechanic | Date: 2026-11-23 | Status: WORKFLOW IMPROVEMENT (option b, team contribution)

## Purpose
The live-leg runbook (`live-leg-runbook-2026-11-20.md`) has 6 items with different preconditions.
A non-sandbox White operator should verify ALL preconditions BEFORE starting so they know which
items are immediately runnable and which need a service brought up first. This file is that check.

## One-command pre-flight (run from non-sandbox White seat)
```
python memory/ops/live_leg_preflight.py
```

Output: per-item GO / BLOCKED with the exact missing precondition. Exit 0 if all GO, exit 1 if any BLOCKED.

## Manual checklist (if script unavailable)
| # | Item | Precondition | Probe |
|---|------|-------------|-------|
| 1 | Researcher #2 residency matrix | :8888 reachable on >=1 host | `python -c "import socket; print(socket.socket().connect_ex(('127.0.0.1',8888)))"` → 0 |
| 2 | Orchestrator #5 binding audit | :8888 reachable | same as above |
| 3 | Orch+Res #1/#3 hotload cycle | elev.py exit 0 + :8888 | `python elev.py whoami` → username (not exit 5) |
| 4 | Verifier #4 perf gate | :8099 reachable | `python -c "import socket; print(socket.socket().connect_ex(('127.0.0.1',8099)))"` → 0 |
| 5 | Mechanic #4 load probe seed | :8099 reachable | same as #4 |
| 6 | Archivist #3 schtask register | COM/schtasks works + all target scripts exist | `schtasks /query /tn PortalFleetProbe` → not "not found" |

## Item independence (can run subset if some preconditions fail)
- Items 1+2 need only :8888 — independent of :8099 and elev.py.
- Items 4+5 need only :8099 — independent of :8888.
- Item 3 needs BOTH elev.py AND :8888.
- Item 6 needs COM (schtasks) + script existence — independent of network ports.

So a partial run is always possible; the pre-flight tells you exactly which subset.

## Credit
Mechanic, auto-loop contribution (option b). Assists Archivist G3 closure by making the final step's precondition explicit and separable from the other 5 items.