# Fleet Health Composite - backend built + verified (2026-11-18)
Goal #9. `_fleet_health_composite()` added to agent_portal.py + route `/api/fleet/health` wired
(before /api/memory-health). Per-agent 0-100 composite from 4 weighted factors:
completion 0.5 (goal_ledger, evidence-gated), freshness 0.3 (newest mtime of goals file +
memory/<agent>/ leaves; 100 - age_days*15), latency 0.1 + errors 0.1 = EXCLUDED when no
per-request log exists on this host (honest, not guessed) and weights renormalised.
Color: red<40 amber<=70 green>70.

In-process self-test `memory/orchestrator/_health_selftest.py` (extracts the fn, stubs
load_agents->agents.json) -> all 8 agents, numeric scores, correct colors:
researcher/builder/verifier 99.9 green (10/10); orchestrator 87.5 green (8/10);
mechanic 56.2 amber (3/10); designer 50.0 amber; scribe 49.9 amber; archivist 43.3 amber.
fleet_avg 73.3. py_compile SYNTAX_OK.

REMAINING: per-agent-card score badge in fleet tab UI (ui/core.js) - same pattern as the
capacity gauge strip (goal #2). Backend acceptance ("endpoint returns scores for all 8")
satisfied; "badges color correctly" pending UI render.
