# Goal 8 Evidence: Cross-Agent Dependency Graph API

**Date:** 2026-11-18
**Goal:** `/api/fleet/dependencies` parses goal files for cross-references and returns a directed graph JSON.

## What was built
- `_fleet_dependencies()` function added to agent_portal.py (after `_list_roster_snapshots`, before `_fleet_health_snapshot`)
- Route `elif p == "/api/fleet/dependencies"` wired in the GET handler after roster-diff route

## How it works
1. Loads agents.json to get the list of agent IDs
2. For each agent's goal file (memory/goals/<agent>.md):
   - Counts total goals (lines matching `^\d+. **`) and open goals (no `(verified:` marker)
   - Scans for explicit cross-references: `AgentName#N` pattern (case-insensitive)
   - Scans for dependency phrases: "needs/depends on/requires AgentName"
3. Deduplicates edges by (from, to, goal_ref) tuple
4. Returns `{nodes: [...], edges: [...], generated_at: ISO}`

## Test results (in-process)
- 8 nodes returned, all with correct open_goals counts matching manual inspection
- 5 edges found:
  - orchestrator → builder (Builder#3, explicit)
  - orchestrator → builder (dependency phrase)
  - verifier → builder (builder#1, explicit)
  - verifier → designer (designer#1, explicit)
  - verifier → scribe (scribe#1, explicit)
- Syntax check: `py_compile` passes

## Remaining for full verification
- Live HTTP call to confirm endpoint returns 200 + valid JSON
- UI: force-directed mini-graph in fleet tab (separate task, can be next cycle)
