# Cycle 15 Goal Proposal - Fleet Autonomy Convergence (2026-11-24)

**Theme:** The loop closes. Cycles 10-14 built the execution layer (playbook runner,
cockpit, model swap, re-routing, health scoring). Cycle 15 makes the system aware of
its own completion state and transitions cleanly between work/maintenance/idle modes
without wasting agent-passes.

**Principle:** Every goal must produce a file or measurement. No "review" goals.

## Per-Seat Goals (10 total, 2 per seat)

### Orchestrator
1. **Dispatch Queue Sync** - `python memory/orchestrator/dispatch_sync.py`: on each
   auto-loop pass, reconcile the dispatch queue with next10.json status field.
   "reached" goals are excluded from dispatch; idle agents get the role-specific
   maintenance task from idle-maintenance-rotation-2026-11-24.md instead of the
   generic (a)(b)(c)(d) menu. Verified: after sync, no agent is dispatched for a
   reached goal in 3 consecutive passes; all idle agents receive role-specific tasks.

2. **Fleet Mode Controller** - `python memory/orchestrator/fleet_mode.py`: determine
   current fleet mode (WORK / MAINTENANCE / IDLE) from goal completion % + time of
   day. Write mode to memory/ops/fleet-mode.json (read by cockpit + dispatch).
   WORK: any agent has open goals. MAINTENANCE: all reached, within 6h of last
   activity. IDLE: all reached, >6h since last activity. Verified: mode transitions
   correctly at 99%->100% and 100%+time threshold; cockpit reads fleet-mode.json.

### Builder
3. **Idle Task Injector** - Modify agent_portal.py dispatch logic: when fleet_mode=
   MAINTENANCE or IDLE, inject the role-specific task from idle-maintenance-rotation
   table into each agent's @Name section (replaces generic menu). Log which task was
   assigned to decision-log.jsonl. Verified: 3 consecutive idle passes show specific
   tasks in dispatch text; at least 5/8 agents produce productive=true.

4. **Cockpit Mode Banner** - Add a top-of-page banner in cockpit showing current
   fleet mode (WORK=green, MAINTENANCE=amber, IDLE=grey) with time-since-last-activity.
   Fetch from /api/fleet/cockpit (add fleet_mode field). Verified: banner renders
   correct color per mode; updates on 30s refresh; visible at 1440px and 768px.

### Researcher
5. **Productivity Baseline** - `python memory/researcher/idle_productivity.py`:
   measure per-agent productive-pass rate over last 24h (file changes / total passes).
   Write to memory/ops/productivity-baseline.json. Flag agents below 30% for 2+ days.
   Verified: script runs <5s; output JSON has per-agent pass_count, productive_count,
   rate; flags are correct on synthetic test data.

6. **Goal Proposal Auto-Generator** - `python memory/researcher/goal_proposer.py`:
   scan decision-log.jsonl + blockers.md + hot notes for recurring patterns (>3
   occurrences of same root cause). Generate a draft cycle proposal (markdown) with
   one goal per pattern, pre-filled with verification criteria. Verified: on real
   data, generates >=3 valid proposals; each has a testable acceptance criterion;
   no duplicates vs closed_topics.json.

### Verifier
7. **Mode Transition Test** - `python memory/verifier/mode_transition_test.py`:
   simulate fleet going 99%->100% and verify: (a) fleet_mode.json updates within
   one pass, (b) dispatch text changes from goal-list to maintenance-task,
   (c) cockpit banner color changes. Verified: all 3 assertions pass on simulated
   transition; total test <2 min.

8. **Idle Pass Auditor** - `python memory/verifier/idle_audit.py`: scan last 50
   auto-loop passes from autoloop.json. Flag any pass where an agent was dispatched
   for a reached goal OR received the generic (a)(b)(c)(d) menu when fleet_mode was
   MAINTENANCE/IDLE. Write report to memory/verifier/idle-audit-report.md.
   Verified: on current data, reports 0 violations after dispatch_sync is deployed;
   on synthetic pre-fix data, correctly flags >=5 violations.

### Designer
9. **Mode-Specific Cockpit Layout** - Design (CSS + JS): in MAINTENANCE mode, cockpit
   panels re-prioritize: Health Score + Productivity Baseline move to top row; Goal
   Progress collapses to a single summary bar. In IDLE mode, show "All goals reached"
   hero + next-cycle countdown. Write design spec + implement in ui/cockpit.js.
   Verified: at 1440px, MAINTENANCE layout shows health+productivity first; IDLE shows
   hero; no overflow at 768px.

10. **Fleet Mode ARIA + Keyboard Nav** - Add ARIA-live region for mode changes (screen
    reader announces "Fleet entered maintenance mode"); ensure all cockpit panels are
    keyboard-navigable in all three modes (Tab order logical, Enter activates).
    Verified: Playwright test confirms aria-live="polite" fires on mode change; Tab
    through all 6+ panels without mouse; no focus traps.

## Sequencing
Week 1: Goals 1-2 (Orchestrator) unblock 3-4 (Builder) which enables 7 (Verifier).
Parallel: 5-6 (Researcher), 9-10 (Designer) independent.
Gate: Goal 3 (Idle Task Injector) is the critical path - everything else depends on it.

## Anti-Duplication Check
- No goal re-issues any entry in closed_topics.json (242 entries checked).
- Distinct from cycle 14's "Closed-Loop Latency Budget" (that measured per-segment
  latency; this addresses mode-awareness and dispatch correctness).
- Builds on idle-maintenance-rotation-2026-11-24.md (Orchestrator spec, already written).

## Risk
- If fleet_mode.json write fails (permissions), system degrades to current behavior
  (generic menu) - no data loss, just wasted passes. Acceptable.
