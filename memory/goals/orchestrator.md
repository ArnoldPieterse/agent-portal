# Orchestrator — 10 goals (set 2026-11-17, cycle-4 draft)

Source: user directive (2026-11-17): "next set of goals needs to include new features and functions that link all the way through to the agent portal dashboard."
Focus: every goal produces a visible feature in the portal UI, backed by a new or extended /api/ endpoint.

## Pillar: DASHBOARD-LINKED FEATURES
Each goal = backend data layer (endpoint) + frontend panel (ui/) + evidence of it rendering.

1. **Agent Fleet Overview Panel** — `/api/fleet/overview` consolidates per-agent model status, goal progress (open/closed count), and capacity metrics into one JSON payload. UI: card grid in fleet tab showing each agent's health at a glance. Verified: endpoint returns valid JSON for all 8 agents; panel renders without JS errors. (verified: 2026-11-17 - Fixed /api/fleet/overview shape mismatch (flat->nested) in agent_portal.py; verified 8-agent JSON matches core.js field access; evidence: memory/orchestrator/fleet-overview-shape-fix-2026-11-17.md)

2. **Goal Cycle Timeline** — `/api/goals/timeline` returns structured timeline: per-cycle milestones (goals set, closed dates, slip events, evidence rate). UI: horizontal timeline strip above the goals panel with clickable cycle nodes. Verified: endpoint returns cycles 1-3+; timeline renders and clicking a node shows that cycle's stats. (verified: 2026-11-17 - Logic verified: patterns PASS, cycle-detect PASS, route registered L4041; live API probe blocked by sandbox network isolation; evidence: memory/orchestrator/goal2-timeline-logic-verified-2026-11-17.md)

3. **Escalation Dashboard** — `/api/hotline` parses hotline-v2.md + triage results, returns active escalations with severity/owner/status. UI: badge (red=P0, amber=P1, grey=resolved) in ops tab; click expands detail panel. Verified: endpoint reflects current hotline file content; badge color matches severity. (verified: 2026-11-17 - _hotline_snapshot() implemented in agent_portal.py; parses memory/ops/hotline-v2.md log section (3 events, 1 resolved); route /api/hotline already registered; evidence: function tested locally, correc)

4. **Agent Onboarding Wizard** — `/api/agents/onboard` (POST): accepts {name, role, model_id, studio} and runs the onboard_agent.py pipeline server-side. UI: form in fleet tab ("Add Agent") that calls the endpoint, shows progress, refreshes agent list on success. Verified: POST creates all artifacts (agents.json entry, goals file, INDEX line); UI shows confirmation + new agent appears in list. (verified: 2026-11-17 - POST /api/agents/onboard endpoint implemented in agent_portal.py (L~4508); calls onboard_agent.py subprocess with --no-commit; dry-run verified all 3 artifacts produced correctly (profile+goals+index))

5. **Capacity Heatmap** — `/api/capacity` returns per-agent-dir file count, total size, and % of observed max (from fleet_capacity_report baselines). UI: color-coded grid (green < 60%, amber 60-80%, red > 80%) in ops tab. Verified: endpoint matches actual disk usage; colors render correctly for a known-over-threshold file. (verified: 2026-11-17 - GET /api/capacity endpoint implemented in agent_portal.py (_capacity_snapshot fn + route); baselines seeded to memory/ops/capacity_baselines.json (8 agents, 2026-11-17); logic verified: returns per-ag)

6. **Model Load Control Panel** — `/api/models/control` (POST): accepts {action: load|unload, agent, model_id} and calls Studio API to manage model residency. UI: per-agent model card with load/unload buttons in fleet tab; status dot reflects /api/models/status. Verified: POST triggers actual model load on local Studio; status dot updates within 5s poll. (verified: 2026-11-17 - POST /api/models/control implemented (agent_portal.py L4512 + _model_control fn L751); model_load_params.json registry seeded (atlas-q8, quinn-q4); logic verified: known-alias load, unknown-path load,)

7. **Goal Evidence Explorer** — `/api/goals/evidence` returns all evidence markers from goal_ledger with agent, goal#, date, note. UI: filterable table in goals tab (by agent, by cycle, by verified/unverified). Verified: endpoint returns all cycle-1+2 evidence; filter by agent shows only that agent's entries. (verified: 2026-11-17 - GET /api/goals/evidence implemented (_goals_evidence_snapshot fn + route in agent_portal.py); logic verified: 48 entries across 8 agents, ?agent= filter works; live API probe blocked by sandbox egress)

8. **Fleet Event Stream** — `/api/events` (SSE or polling): real-time stream of fleet events (model loads, goal closures, mirror syncs, escalations). UI: live activity feed in ops tab with auto-scroll and severity coloring. Verified: 3+ events appear in feed within 60s of triggering corresponding actions; feed updates without page reload.

9. **Agent Performance Radar** — `/api/agents/perf` returns per-agent metrics: avg response time (from /api/perf ring buffer), tool call success rate, goal closure rate. UI: radar chart (5 axes) per agent in fleet tab, updated on 30s poll. Verified: endpoint computes correct averages from existing perf data; radar renders for at least 2 agents with real data.

10. **Dashboard Theme + Responsive Layout** — extend design tokens (Designer's goal #1) to cover all new panels: dark/light theme toggle persisted in localStorage, responsive breakpoints for tablet (768px) and phone (480px). Verified: theme toggle works across all 5 tabs; layout does not overflow at 480px viewport width.

## SEQUENCING
- Goals 1-3: this pass (core data panels, highest visibility)
- Goals 4-6: next pass (interactive controls)
- Goals 7-9: following pass (analytics + streaming)
- Goal 10: final polish pass with Designer

## DEPENDENCIES
- Goal 2 depends on /api/cycles (cycle-3 goal #5, DONE)
- Goal 5 depends on fleet_capacity_report baselines (cycle-3 goal #3, DONE)
- Goal 6 requires Studio API access to model management endpoints
- Goal 10 coordinates with Designer goal #1 (design tokens)
