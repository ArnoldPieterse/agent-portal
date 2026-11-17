# Fleet Overview Panel (/api/fleet/overview) — end-to-end verification
Date: 2026-11-17 | Verifier (assisting Orchestrator cycle-4 Goal 1)
Suite: dashboard-linkage / goal-1-fleet-overview
Result: **PASS (logic + capacity)** + 2 findings (1 structural, 1 data-freshness)
Evidence path: this file. Method: in-process call to real `_fleet_overview()`.

## What was tested (and how)
Live HTTP round-trip is NOT possible from the agent sandbox: python-sandbox egress is
allowlist-blocked and host loopback returns WinError 10013 (firewall/WFP on :8099).
Recorded once, not re-probed. So I invoked the REAL endpoint function in-process:
- `importlib` load of agent_portal.py with a one-line shim: `os.listdir` swallows
  PermissionError (module-level `_find_sandbox_dir()` lists C:\Users, denied in-sandbox;
  env artifact, not a code bug). No other code modified.
- Stubbed only `ap._model_load_status = lambda: {}` (isolates the network probe; sandbox
  has no egress). Goals + capacity logic runs unmodified.
- Ground truth computed independently: capacity via own `os.walk`; goals via the same
  SSOT parser `goal_ledger.parse_agent_file` (identical to /api/goals by construction).

## Verdict per layer
1. GOAL AGGREGATION LOGIC — **PASS**. endpoint `goals_done` == parse_agent_file done for
   all 8 agents (Orchestrator 0, Researcher 8, Builder 10, Verifier 10, Designer 2,
   Archivist 2, Scribe 6, Mechanic 1). No aggregation bug; panel is consistent with /api/goals.
2. CAPACITY — **PASS 8/8 exact**. endpoint files+kb == independent os.walk for every agent
   (e.g. Builder 144 files/3450.1KB, Designer 262/3419.4KB). Fleet totals: agents_total=8,
   goals 39/80, fleet_pct=48.8 — all internally consistent.

## Finding A (structural / dead field)
`goals_blocked` is ALWAYS 0 on the dashboard. Root cause: `parse_agent_file` never emits a
`"blocked"` key, so `g.get("blocked", False)` in `_fleet_overview` is structurally False.
The per-agent "blocked" column can never be non-zero.
Fix (Orchestrator/Builder): either make parse_agent_file detect `(blocked:` / `[BLOCKED]`
markers and set g["blocked"]=True, or drop the field from endpoint + UI card.

## Finding B (data-freshness / SSOT divergence)
Dashboard reads `memory/goals/<name>.md` (SSOT), NOT TODO.md. For Orchestrator the two have
diverged: memory/goals/orchestrator.md is the cycle-4 DRAFT with all 10 goals still unmarked
(evidence_via=-, status=open) -> panel shows 0/10. But TODO.md live cycle-4 section already has
Goal 1 (Fleet Overview Panel) as `[x] ... (verified: ...)`. So the panel UNDERSTATES real progress.
Fix (Orchestrator): back-propagate cycle-4 goal completions into memory/goals/orchestrator.md
with evidence markers, OR declare TODO.md scratch-only and the goal file canonical.

## Residual (untested)
- Live HTTP transport + JSON serialization over the wire: not exercised (egress block).
  Covered by inspection of do_GET routing (line ~3892) + _json(). Low risk.
- model_status field path: stubbed this run; live per-host probe untested in-sandbox.

Command (reproducible, host terminal or sandbox):
  python -c "<see memory/verifier/fleet-overview-verify script>" — see chat for full script.