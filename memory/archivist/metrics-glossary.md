# Fleet Autonomy Metrics Glossary (cycle 15)

Formal definitions of the metrics the fleet uses to judge itself. Every entry:
name, formula, units, source data, threshold. No approximations.

## 1. Productive pass
- Formula: `productive = 1` iff the pass's `why_bits` contain at least one seat with a queued human message (`<seat>:queued-msg`) or an open-goal task (`<seat>:N-open`, N>0); otherwise `0`.
- Units: dimensionless (0/1 per pass).
- Source: `memory/orchestrator/autoloop.json` -> `last_pass.productive`, `last_pass.why_bits`.
- Threshold: a maintenance-only batch is non-productive; 3+ consecutive non-productive passes at 100% triggers the pass-budget pause (see 6).

## 2. Convergence velocity
- Formula: `(reached_now - reached_start) / (t_now - t_start)` over one cycle, where `reached` = count of goal lines carrying a `(verified:)` or `(pointer:)` marker.
- Units: goals/hour.
- Source: `memory/goals/*.md` parsed by `memory/orchestrator/fleet_mode.py::parse_goal_status`; cycle boundaries from `memory/levels/level_N_*.md`.
- Threshold: >= 2 goals/h sustained across a full cycle is healthy; < 0.5 goals/h flags a stall (check blockers.md).

## 3. Idle waste
- Formula: `sum(pass_duration_s for passes where productive == 0) / total_idle_window_s`.
- Units: fraction of idle time (0..1), reported as %.
- Source: `autoloop.json` pass log (timestamps + productive flag); idle window = span between the moment the fleet first hit 100% and the next goal ratification.
- Threshold: < 25% of idle time is acceptable; above that, the rotation table (memory/ops/idle-maintenance-rotation*.md) must be widened.

## 4. Mode duration
- Formula: for mode M, `sum(t_switch_out - t_switch_in)` over all intervals where `fleet-mode.json.mode == M`.
- Units: hours per mode per cycle.
- Source: `memory/ops/fleet-mode.json` (mode + timestamp), transition history in the same file's log array.
- Threshold: MAINTENANCE > 4h while any agent holds open goals = dispatch bug; IDLE > 2h without a queued human message = expected but logged.

## 5. Dispatch correctness rate
- Formula: `goals_completed_via_dispatch / dispatches_issued`, where a dispatch counts when an autoloop pass hands a seat its oldest open goal and the seat later records `(verified:)` on that goal within 24h.
- Units: fraction (0..1), reported as %.
- Source: `autoloop.json` sections (seat -> task) + timestamped evidence lines in `memory/goals/*.md`.
- Threshold: >= 80% per cycle; below that, review pass prompt wording and PASS_TIMEOUT_S.

## 6. Pass budget
- Formula: `streak = count of consecutive non-productive passes`; budget exhausted when `streak >= AUTOLOOP_MAX_STREAK`. Any productive pass resets `streak` to 0.
- Units: integer streak; constant `AUTOLOOP_MAX_STREAK` in `agent_portal.py`.
- Source: `autoloop.json` -> `streak`; constants block near the AUTOLOOP section of `agent_portal.py`.
- Threshold: pause fires exactly at the constant (never earlier); a pause must never gate a pass that carries real work.

## 7. Fleet completion rate
- Formula: `reached / total` over all agents, same markers as metric 2.
- Units: fraction (0..1), reported as %.
- Source: `fleet_mode.py::get_goal_stats()`; served live at `/api/goals`.
- Threshold: 100% gates the level counter (`memory/levels.json`); any single agent below 100% blocks the gate.

## 8. Maintenance cooldown efficiency
- Formula: `rotation_tasks_done / maintenance_passes_at_100pct`, where a rotation task counts when the pass body contained a role-specific task from the rotation table and the seat recorded evidence for it.
- Units: fraction (0..1), reported as %.
- Source: pass bodies in `autoloop.json` + evidence lines in `memory/goals/*.md`; rotation table at `memory/ops/idle-maintenance-rotation-2026-11-24.md`.
- Threshold: >= 50% of maintenance passes should execute the assigned rotation task; below that, tasks are too long or poorly scoped.
