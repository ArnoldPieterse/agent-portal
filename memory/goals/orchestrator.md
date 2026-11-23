# Orchestrator — Cycle 15 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Mode Controller, (2) Dispatch Correctness, (3) Idle Productivity

1. **Fleet Mode Controller** - `python memory/orchestrator/fleet_mode.py`: determine current fleet mode (WORK / MAINTENANCE / IDLE) from goal completion % + time-since-last-activity. Write to memory/ops/fleet-mode.json (SSOT read by cockpit + dispatch). WORK: any agent has open goals. MAINTENANCE: all reached, <6h since last activity. IDLE: all reached, >6h. Verified: mode transitions correctly at 99%->100% and 100%+time threshold; fleet-mode.json exists with valid schema after each run.

2. **Dispatch Queue Sync** - `python memory/orchestrator/dispatch_sync.py`: on each auto-loop pass, reconcile dispatch queue with next10.json status field. "reached" goals excluded from dispatch; idle agents get role-specific maintenance task from idle-maintenance-rotation table instead of generic menu. Verified: after sync, no agent dispatched for a reached goal in 3 consecutive passes; all idle agents receive role-specific tasks (logged to decision-log.jsonl).

3. **Idle Maintenance Rotation** - Write memory/ops/idle-maintenance-rotation.md: table mapping each role -> 5 rotating maintenance tasks (e.g., Researcher: "re-run stale_claim_scan", Builder: "check for orphaned temp files"). Rotation advances daily. Verified: file exists with 8 roles x 5 tasks; dispatch references correct task for current day-of-cycle; no two consecutive passes assign same task to same agent.

4. **Mode Transition Log** - Append every fleet-mode change to memory/ops/mode-transitions.jsonl with fields: timestamp, from_mode, to_mode, trigger (goal_pct, elapsed), goal_count_open. Verified: after 3 simulated transitions, JSONL has 3 entries with correct from/to/trigger; no gaps in sequence.

5. **Auto-Loop Pass Budget** - Define per-cycle pass budget (default: 200 total agent-passes). Track consumption in memory/ops/pass-budget.json. When budget exhausted, force fleet to IDLE mode and stop dispatching WORK tasks. Verified: budget file increments correctly per pass; at 200/200, next dispatch returns no WORK tasks; mode transitions to IDLE automatically. (pointer: memory/orchestrator/goal9-cycle-cost-tracker-2026-11-20.md)

6. **Goal Cycle Auto-Close** - `python memory/orchestrator/cycle_auto_close.py`: when all goals reach 100%, auto-execute: (a) archive old goal files to memory/goals/archive/, (b) write GOAL_RESET_PENDING.json, (c) trigger next goal-setting round prompt. Verified: on synthetic 100% state, all 3 actions execute in order; archive contains timestamped copies; reset file has correct schema. (pointer: memory/orchestrator/pin-sha-stale-ref-fix-2026-11-17.md)

7. **Seat Availability Router** - When a seat is unreachable at run start, re-route its open goals to the nearest available agent with matching capability (defined in memory/ops/seat-routing-map.json). Log re-route decision. Verified: with 1 simulated unreachable seat, its 2 open goals appear in another agent's dispatch list; routing map exists with all 8 seats mapped.

8. **Mode-Aware Prompt Context** - Inject current fleet mode + open-goal count into each agent's system prompt context block (via agent_portal.py prompt assembly). Agents see "FLEET MODE: MAINTENANCE | Open goals: 0 | Your task: [specific]". Verified: in MAINTENANCE mode, prompt contains mode label + specific task (not generic menu); in WORK mode, prompt contains open goal list.

9. **Productive Pass Gate** - Before marking an auto-loop pass as complete, verify the agent produced at least one file change OR measurement output (check mtime delta in memory/). If not productive, flag pass as "wasted" in autoloop.jsonl. Verified: on a synthetic no-op pass, gate flags productive=false; on a pass with file write, productive=true; flag appears in JSONL.

10. **Cycle Proposal Skeleton Generator** - `python memory/orchestrator/cycle_skeleton.py`: at cycle close, auto-generate next-cycle proposal skeleton from: (a) completed goals (what worked), (b) open patterns from decision-log, (c) round_topic.json queue. Write to memory/goals/cycle{N+1}-skeleton.md. Verified: on real cycle-14 data, generates a skeleton with >=5 goal stubs, each referencing a concrete pattern or completed capability; no duplicates vs closed_topics.json.
