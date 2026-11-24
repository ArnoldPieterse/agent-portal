"""
End-to-End Mode Cycle Test
===========================
Full simulation: WORK (5 open goals) -> complete goals -> MAINTENANCE (6h wait)
-> IDLE -> new cycle starts -> WORK again.

Verifies all transitions, dispatch changes, banner updates, and productivity
tracking throughout the full cycle.

Usage:
  python memory/verifier/e2e_mode_cycle.py
"""
import json, sys, pathlib, tempfile, os, shutil
from datetime import datetime, timezone, timedelta
from io import StringIO

# --- Minimal in-memory simulation of fleet components ---

class FleetState:
    """Simulated fleet state for e2e testing."""
    def __init__(self):
        self.mode = 'WORK'
        self.goals = []  # list of {id, lane, status, reached_at}
        self.transitions = []  # mode transition log
        self.dispatch_log = []  # dispatch entries per pass
        self.productivity = {}  # agent -> {total, productive}
        self.banner_color = 'green'  # WORK=green, MAINTENANCE=amber, IDLE=grey
        self.last_activity = datetime.now(timezone.utc)
        self.cycle_number = 15

    def add_goals(self, goals):
        self.goals.extend(goals)

    def complete_goal(self, goal_id, ts):
        for g in self.goals:
            if g['id'] == goal_id:
                g['status'] = 'reached'
                g['reached_at'] = ts.isoformat()

    def pct_complete(self):
        if not self.goals:
            return 0.0
        reached = sum(1 for g in self.goals if g['status'] == 'reached')
        return round(reached / len(self.goals) * 100, 1)

    def transition_to(self, new_mode, trigger, ts):
        """Execute a mode transition."""
        old = self.mode
        self.transitions.append({
            'from': old, 'to': new_mode,
            'trigger': trigger, 'timestamp': ts.isoformat()
        })
        self.mode = new_mode
        # Update banner color
        self.banner_color = {'WORK': 'green', 'MAINTENANCE': 'amber', 'IDLE': 'grey'}[new_mode]
        self.last_activity = ts

    def generate_dispatch(self, now):
        """Generate dispatch for current mode."""
        if self.mode == 'WORK':
            tasks = [g['id'] for g in self.goals if g['status'] == 'open']
        elif self.mode == 'MAINTENANCE':
            tasks = ['maint:re-run-stale-claims', 'maint:check-disk-space']
        else:  # IDLE
            tasks = ['idle:standby']
        entry = {'timestamp': now.isoformat(), 'mode': self.mode, 'tasks': tasks}
        self.dispatch_log.append(entry)
        return entry

    def record_pass(self, agent, productive):
        if agent not in self.productivity:
            self.productivity[agent] = {'total': 0, 'productive': 0}
        self.productivity[agent]['total'] += 1
        if productive:
            self.productivity[agent]['productive'] += 1


def run_e2e_cycle():
    """Run the full e2e mode cycle simulation. Returns (state, results)."""
    state = FleetState()
    results = []
    t0 = datetime(2026, 11, 24, 8, 0, 0, tzinfo=timezone.utc)

    # === PHASE 1: WORK with 5 open goals ===
    phase1_goals = [
        {'id': 'v1', 'lane': 'verifier', 'status': 'open', 'reached_at': None},
        {'id': 'b1', 'lane': 'builder', 'status': 'open', 'reached_at': None},
        {'id': 'r1', 'lane': 'researcher', 'status': 'open', 'reached_at': None},
        {'id': 'd1', 'lane': 'designer', 'status': 'open', 'reached_at': None},
        {'id': 's1', 'lane': 'scribe', 'status': 'open', 'reached_at': None},
    ]
    state.add_goals(phase1_goals)

    # Verify initial state
    r = (state.mode == 'WORK' and state.pct_complete() == 0.0 and state.banner_color == 'green')
    results.append(('P1_initial_work_state', r))

    # Dispatch in WORK mode -> should list all 5 open goals
    t1 = t0 + timedelta(minutes=5)
    d1 = state.generate_dispatch(t1)
    r = (len(d1['tasks']) == 5 and d1['mode'] == 'WORK')
    results.append(('P1_dispatch_5_open_goals', r))

    # Record some productive passes
    for agent in ['verifier', 'builder', 'researcher']:
        state.record_pass(agent, productive=True)
        state.record_pass(agent, productive=False)  # one wasted each
    r = (state.productivity['verifier']['total'] == 2 and
         state.productivity['verifier']['productive'] == 1)
    results.append(('P1_productivity_tracking', r))

    # === PHASE 2: Complete all goals -> trigger MAINTENANCE ===
    t2 = t0 + timedelta(hours=3)
    for g in phase1_goals:
        state.complete_goal(g['id'], t2)

    # Verify 100% complete
    r = (state.pct_complete() == 100.0)
    results.append(('P2_all_goals_reached_100pct', r))

    # Trigger transition to MAINTENANCE
    state.transition_to('MAINTENANCE', 'goal_pct=100%', t2)
    r = (state.mode == 'MAINTENANCE' and state.banner_color == 'amber')
    results.append(('P2_transition_to_maintenance', r))

    # Dispatch in MAINTENANCE -> maintenance tasks, NOT goal tasks
    t3 = t2 + timedelta(minutes=10)
    d2 = state.generate_dispatch(t3)
    r = (d2['mode'] == 'MAINTENANCE' and len(d2['tasks']) == 2 and
         all('maint:' in t for t in d2['tasks']))
    results.append(('P2_maintenance_dispatch', r))

    # No overlap with goal tasks
    r = not any(t in [g['id'] for g in phase1_goals] for t in d2['tasks'])
    results.append(('P2_no_goal_overlap_in_maint', r))

    # === PHASE 3: 6h wait -> IDLE ===
    t4 = t2 + timedelta(hours=6)
    state.transition_to('IDLE', 'elapsed>6h in MAINTENANCE', t4)
    r = (state.mode == 'IDLE' and state.banner_color == 'grey')
    results.append(('P3_transition_to_idle', r))

    # Dispatch in IDLE -> standby only
    d3 = state.generate_dispatch(t4 + timedelta(minutes=5))
    r = (d3['mode'] == 'IDLE' and d3['tasks'] == ['idle:standby'])
    results.append(('P3_idle_standby_dispatch', r))

    # Record idle passes (non-productive)
    for agent in ['verifier', 'builder']:
        state.record_pass(agent, productive=False)
    r = (state.productivity['verifier']['total'] == 3 and
         state.productivity['verifier']['productive'] == 1)  # still only 1 productive
    results.append(('P3_idle_passes_not_productive', r))

    # === PHASE 4: New cycle starts -> WORK again ===
    t5 = t4 + timedelta(hours=2)
    state.cycle_number += 1  # cycle 16
    state.goals = [
        {'id': 'v_new1', 'lane': 'verifier', 'status': 'open', 'reached_at': None},
        {'id': 'b_new1', 'lane': 'builder', 'status': 'open', 'reached_at': None},
    ]
    state.transition_to('WORK', f'new_cycle_{state.cycle_number} started', t5)
    r = (state.mode == 'WORK' and state.banner_color == 'green' and
         state.pct_complete() == 0.0)
    results.append(('P4_new_cycle_work_resumes', r))

    # Dispatch in new WORK cycle -> new goals only
    d4 = state.generate_dispatch(t5 + timedelta(minutes=5))
    r = (d4['mode'] == 'WORK' and len(d4['tasks']) == 2 and
         set(d4['tasks']) == {'v_new1', 'b_new1'})
    results.append(('P4_new_goals_dispatched', r))

    # === FINAL: Verify transition log integrity ===
    # Should have exactly 3 transitions: WORK->MAINT, MAINT->IDLE, IDLE->WORK
    r = (len(state.transitions) == 3)
    results.append(('F_transition_count_3', r))

    # Each transition has valid fields
    all_valid = all(
        t['from'] in ('WORK','MAINTENANCE','IDLE') and
        t['to'] in ('WORK','MAINTENANCE','IDLE') and
        t['from'] != t['to'] and
        'timestamp' in t and 'trigger' in t
        for t in state.transitions
    )
    results.append(('F_transitions_valid_fields', all_valid))

    # Banner color sequence: green -> amber -> grey -> green
    colors = ['green']  # initial
    for t in state.transitions:
        colors.append({'WORK':'green','MAINTENANCE':'amber','IDLE':'grey'}[t['to']])
    r = (colors == ['green', 'amber', 'grey', 'green'])
    results.append(('F_banner_color_sequence', r))

    # Dispatch log has entries for all 4 phases
    modes_seen = [d['mode'] for d in state.dispatch_log]
    r = ('WORK' in modes_seen and 'MAINTENANCE' in modes_seen and 'IDLE' in modes_seen)
    results.append(('F_dispatch_log_all_modes', r))

    # Productivity: verifier had 3 total, 1 productive (~33% rate)
    r = (round(state.productivity['verifier']['productive'] / state.productivity['verifier']['total'], 4) == round(1/3, 4))
    results.append(('F_productivity_rate_correct', r))

    return state, results


def main():
    print("E2E MODE CYCLE TEST")
    print("=" * 60)
    state, results = run_e2e_cycle()

    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {name}")

    elapsed_note = f"({len(results)} assertions)"
    print("-" * 60)
    print(f"RESULT: {'PASS' if all_pass else 'FAIL'} {elapsed_note}")
    trans_str = " -> ".join(f"{t['from']}->{t['to']}" for t in state.transitions)
    print(f"  Transitions: {trans_str}")
    print(f"  Final mode: {state.mode}, cycle: {state.cycle_number}")

    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
