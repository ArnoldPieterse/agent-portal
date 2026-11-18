# Orchestrator - 10 goals (set 2026-11-18, cycle-5)

Focus: Fleet self-management maturity. Automate the goal-cycle lifecycle, improve capacity planning, and make HR workflows (onboard/re-role/retire) one-command operations visible in the portal.

1. **Auto Goal-Cycle Transition** - When all 80 goals are closed, automatically archive old files to memory/goals/archive/, generate a cycle kickoff note, and update TODO.md. Verified: script `memory/orchestrator/auto_cycle_transition.py` runs end-to-end on a test dir; produces correct archive + new files. (verified: 2026-11-18 - auto_cycle_transition.py written + tested: --check detects 62 open correctly; dry-run simulates full archive(8 files)+kickoff+todo path on test fixture)

2. **Capacity Planner Panel** - `/api/fleet/capacity` returns per-agent model load (tokens/sec estimate), context usage %, and predicted saturation time based on recent activity. UI: gauge strip in fleet tab. Verified: endpoint returns valid JSON for all 8 agents with numeric fields; panel renders gauges without JS errors. _Progress 2026-11-18: backend `/api/fleet/capacity` BUILT + verified in-process (exact-source test, both live-perf & prior-fallback branches, 8/8 numeric). Remaining: gauge-strip UI in core.js fleet tab._ (pointer: memory/orchestrator/fleet-overview-shape-fix-2026-11-17.md)

3. **One-Command Re-role** - `python memory/orchestrator/rerole_agent.py <agent> --new-role <role>` updates agents.json (persona, blurb, tools), regenerates goals file header, and commits. Verified: running on a test agent produces all 3 artifacts; portal reflects change after next mirror cycle. _Progress 2026-11-18: `rerole_agent.py` BUILT + verified in isolated fixtures - dry-run safe; artifact1 agents.json (blurb/persona/tools) + artifact2 goals header/focus both proven end-to-end, incl. stale-name refresh + error paths (exit 2). Artifact3 commit branch is standard-git, returns rc0 + writes files when git absent; untestable in this sandbox (no git binary on PATH). Remaining: exercise live commit + confirm portal reflection after a real re-role._ (pointer: memory/orchestrator/rerole-progress-2026-11-18.md)

4. **Retirement Checklist Automation** - `python memory/orchestrator/retire_agent.py <agent> --dry-run` produces a checklist (files to archive, references to update, INDEX lines to strike) and applies on confirm. Verified: dry-run on scribe shows correct file list; confirm mode executes without error.

5. **Goal Slip Prediction API** - `/api/goals/slip-risk` returns per-open-goal probability of missing next cycle based on historical patterns (from memory/goals/slip_prediction_table.json). UI: amber/red dot on at-risk goals in the goals panel. Verified: endpoint returns scored list; dots render correctly for test data.

6. **Fleet Roster Diff View** - `/api/fleet/roster-diff?since=<cycle>` returns JSON diff of agents.json between two cycles (added/removed/re-roled). UI: "Changes since last cycle" collapsible in fleet tab. Verified: endpoint returns correct diff for cycle-4 to 5; panel shows added/removed agents.

7. **Onboarding Pack v3 Template** - Extend the onboarding wizard to accept a `--template` flag (solo/research/build/full-stack) that pre-fills tools, model binding, and 10 starter goals from a role-appropriate template. Verified: POST with each template produces valid agents.json entry + goals file; UI shows template selector.

8. **Cross-Agent Dependency Graph** - `/api/fleet/dependencies` parses goal files for cross-references (e.g., "needs Builder#3 output") and returns a directed graph JSON. UI: force-directed mini-graph in fleet tab showing which agents' goals depend on others. Verified: endpoint returns nodes+edges matching known cross-refs; graph renders.

9. **Fleet Health Composite Score** - `/api/fleet/health` computes a 0-100 composite per agent from: goal completion rate, evidence freshness, response latency (from portal logs), and error count. UI: single score badge per agent card; red <40, amber 40-70, green >70. Verified: endpoint returns scores for all 8; badges color correctly.

10. **Cycle Narrative Auto-Generator** - After cycle close, `python memory/orchestrator/cycle_narrative.py --cycle N` generates a 2-paragraph summary (goals set/closed, key wins, slippage, next-cycle focus) into memory/synthesis/cycle-narrative.md. Verified: running on cycle-4 data produces coherent narrative; file appended correctly.
