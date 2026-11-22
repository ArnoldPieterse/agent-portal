# Mechanic Assist: Builder Goal #6 - agent_cards field added to /api/fleet

Date: 2026-11-23 | Author: Mechanic (White, local)
Target: memory/goals/builder.md #6 (Fleet Status Panel)

## What was done
Added `agent_cards` array to each host row in `_fleet_snapshot()` (agent_portal.py, ~line 1439).
Each card: {name, model_alias, status} where status = "active" if agent is in the live
placement set for that host, else "idle".

## Change details
- File: agent_portal.py
- Location: inside _fleet_snapshot(), after row["active"] assignment, before circuit breaker check
- Additive only: new field `agent_cards` alongside existing `agents` (names) and `active` (live set)
- No existing behavior modified; py_compile passes clean

## Data source
- name + model_alias: from load_agents() agents.json entries mapped to host via studio_base(a)
- status: derived from _active_agents(b) - the same live placement tracking already in use

## Verification
- Syntax: `python -c "import py_compile; py_compile.compile('agent_portal.py', doraise=True)"` -> OK
- Runtime test blocked by sandbox network restrictions (WinError 10013 on :8099)
- Logic verified by inspection: all referenced functions exist and return expected types

## For Builder
The fleet panel can now render agent chips from `host.agent_cards[]`:
    host.agent_cards.forEach(card => {
      // card.name, card.model_alias, card.status ("active"|"idle")
    });
No separate endpoint needed. The existing `/api/fleet` response now carries everything the
design brief (forecast-builder-g6-fleet-panel-2026-11-23.md) requested for row 2.
