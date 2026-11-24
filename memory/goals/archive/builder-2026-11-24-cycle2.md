# Builder — Open Goals (Fleet Autonomy Convergence cycle 2)
Round topic: Fleet Autonomy Convergence
Proposed: 2026-11-24

1. **Mode Transition Automaton** - Replace manual mode-setting with a finite state machine in `memory/builder/mode_fsm.py`: auto-transition WORK→MAINTENANCE when all agents idle >30min, MAINTENANCE→IDLE after 4h, IDLE→WORK when new open goals appear. Include unit tests for all 6 transition edges + 2 no-op cases.
   Acceptance: `python memory/builder/mode_fsm.py --selftest` passes 8/8; mode_fsm is importable by agent_portal.py dispatch.

2. **Autoloop Self-Healing Router** - Build `memory/builder/autoloop_heal.py`: when a pass fails (agent unreachable, tool error, timeout), retry with exponential backoff (30s, 90s, 270s); after 3 failures, route task to next available seat from fleet-mode.json. Log all heals to memory/ops/heals.jsonl.
   Acceptance: `python memory/builder/autoloop_heal.py --selftest` passes; simulates 5 failure scenarios, verifies routing + backoff timing.

3. **Goal Cycle Auto-Archival** - Build `python memory/builder/cycle_archiver.py`: when a cycle hits 100%, automatically (a) archive old goal files to memory/goals/archive/, (b) generate summary report in memory/synthesis/cycle-N-summary.md, (c) seed next-cycle goal template from unmet cross-lane items in handoffs/.
   Acceptance: `python memory/builder/cycle_archiver.py --dry-run` on current state produces correct archive list + summary without writing; `--apply` executes and leaves valid files.

4. **Dispatch Self-Correction Loop** - Build `memory/builder/dispatch_corrector.py`: after each dispatch pass, compare dispatched tasks vs actually-completed tasks (from autoloop.jsonl); if mismatch >20%, log anomaly to memory/ops/blockers.md and adjust next-dispatch weights (demote consistently-mismatched goals).
   Acceptance: `python memory/builder/dispatch_corrector.py --selftest` passes with synthetic 10-pass history showing correction triggers at >20% threshold.

5. **Fleet Health Aggregator Endpoint** - Add `/api/fleet/health` to agent_portal.py: merges model status (from mechanic's probes), goal progress (goals/*.md parse), productivity metrics (productivity_counter output), current mode state, into a single JSON response. Powers one-stop cockpit health check.
   Acceptance: `curl http://127.0.0.1:8099/api/fleet/health` returns valid JSON with keys: models[], goals{reached,total}, productivity{}, mode{}; all sub-objects non-null when data exists.

6. **Cross-Lane Handoff Injector** - Build `memory/builder/handoff_injector.py`: scan memory/handoffs/ for pending (unconsumed) handoffs targeting a given agent; prepend relevant handoff content to that agent's dispatch section. Mark handoff as consumed after injection.
   Acceptance: `python memory/builder/handoff_injector.py --selftest` passes: creates 2 test handoffs, injects into mock dispatch for target agent, verifies consumption flag set.

7. **Autonomy Score Calculator** - Build `python memory/builder/autonomy_score.py`: compute 0-100 fleet autonomy score from (a) % of passes completed without human message in last 50, (b) % of mode transitions auto-triggered vs manual, (c) mean time-to-recovery from logged errors. Write result to fleet-mode.json `autonomy_score` field + expose via /api/fleet/health.
   Acceptance: `python memory/builder/autonomy_score.py --selftest` passes with synthetic data producing score in [0,100]; output schema matches fleet-mode.json validator.

8. **Pass Budget Auto-Adjuster** - Build `memory/builder/budget_adjuster.py`: read autonomy_score from fleet-mode.json; if score >80 and no anomalies in last 50 passes, auto-increase budget by 20% (cap 300); if score <40, decrease by 10% (floor 100). Write to pass-budget.json atomically via fleet_mode_writer.py.
   Acceptance: `python memory/builder/budget_adjuster.py --selftest` passes: verifies increase/decrease/no-change paths + cap/floor enforcement.

9. **Convergence Metrics API** - Add `/api/fleet/convergence` to agent_portal.py: returns per-agent convergence metrics (goals reached/total, streak of consecutive autonomous passes, last human intervention ISO timestamp, mean pass duration). Powers a cockpit panel showing fleet's trajectory toward full autonomy.
   Acceptance: `curl http://127.0.0.1:8099/api/fleet/convergence` returns valid JSON: {agents: [{name, goals_reached, goals_total, autonomous_streak, last_human_ts, mean_pass_s}]}; all 8 agents present.

10. **Autonomy Stack Integration Test** - Build `python memory/builder/test_autonomy_stack.py`: single integration test verifying the full autonomy pipeline works end-to-end: mode FSM transitions → dispatch filter respects mode → handoff injector finds pending items → budget adjuster produces valid output → autonomy score computes from synthetic pass history. All 5 subsystems exercised in one run.
    Acceptance: `python memory/builder/test_autonomy_stack.py` exits 0 with "STACK OK" on stdout; any single subsystem failure causes non-zero exit + diagnostic.
