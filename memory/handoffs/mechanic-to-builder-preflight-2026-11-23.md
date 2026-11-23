# Handoff: runbook_preflight.py -> Builder Goal #10 (One-Click Runbook Trigger)

Date: 2026-11-23
From: Mechanic
To: Builder

## What I built

`memory/mechanic/runbook_preflight.py` - a pre-flight validation module for the one-click
runbook trigger endpoint. Self-test: **11/11 PASS** (offline, no network needed).

## Integration (3 lines in your POST /api/runbooks/trigger handler)

```python
import sys; sys.path.insert(0, "memory/mechanic")
from runbook_preflight import preflight

result = preflight(agent_id, runbook_name)
if not result["ok"]:
    return json_response({"error": "preflight_failed", "reasons": result["reasons"]}, status=409)
# ... proceed to execute runbook ...
```

## What it checks (in order)

| Check | Source | Pass condition |
|-------|--------|----------------|
| `agent_available` | agents.json | agent ID exists; model_loaded != False |
| `host_reachable` | TCP connect to host:port (from studio URL) | port 8888 or 8099 accepts connection within 3s |
| `no_conflict` | `.runbook_active.lock` + decision-log.jsonl | no active lock on same agent; no unended runbook_start in last 5 min |

## Notes for your endpoint

- The lock file (`memory/ops/.runbook_active.lock`) should be written by your playbook_runner
  at start and deleted at end. Format: `{"agent": "id", "runbook": "name", "ts": epoch}`.
- If the decision-log gets a `type: "runbook_start"` / `"runbook_end"` pair, that's also respected.
- Stale locks (>10 min) are auto-ignored - no manual cleanup needed.
- The module is pure stdlib (json, socket, time, pathlib) - no dependencies to install.

## Evidence

- Self-test: `python memory/mechanic/runbook_preflight_selftest.py` -> 11/11 PASS
- Live run from sandbox: agent check PASS, host check FAIL (WinError 10013 - expected in sandbox)
- File: `memory/mechanic/runbook_preflight.py` (~180 lines)
