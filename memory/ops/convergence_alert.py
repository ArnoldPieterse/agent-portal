#!/usr/bin/env python3
"""Convergence Deceleration Alert - monitors velocity per metric across cycles.

Computes velocity (rate of change) for autonomy score, efficiency index, and
intervention count across the last 3+ available cycles. If any metric decelerates
(worsens) for 2+ consecutive cycles, writes an alert to memory/ops/alerts.jsonl.

Usage:
    python memory/ops/convergence_alert.py           # run check
    python memory/ops/convergence_alert.py --selftest  # verify with synthetic data
"""
import json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALERTS_PATH = ROOT / 'memory' / 'ops' / 'alerts.jsonl'
CYCLE_HISTORY = ROOT / 'memory' / 'ops' / 'cycle-history-consolidated.jsonl'
EFFICIENCY_INDEX = ROOT / 'memory' / 'ops' / 'cycle-efficiency-index.jsonl'
AUTONOMY_SCORE = ROOT / 'memory' / 'ops' / 'autonomy-score.json'

# Metric direction: True means higher is better (negative delta = worsening)
METRIC_DIRECTION = {
    'autonomy': True,       # score goes up = good
    'efficiency': True,     # index goes up = good
    'intervention': False,  # count goes down = good
}


def load_jsonl(path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    lines = path.read_text(encoding='utf-8').strip().split('\n')
    results = []
    for line in lines:
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return results


def collect_metrics():
    """Gather per-cycle metrics from available sources. Returns {cycle: {metric: value}}."""
    cycles = {}

    # 1) Cycle history consolidated (has completion_pct, intervention_count)
    for rec in load_jsonl(CYCLE_HISTORY):
        c = rec.get('cycle')
        if c is None:
            continue
        if c not in cycles:
            cycles[c] = {}
        if rec.get('completion_pct') is not None:
            cycles[c]['efficiency'] = rec['completion_pct']

    # 2) Efficiency index (more precise efficiency metric)
    for rec in load_jsonl(EFFICIENCY_INDEX):
        c = rec.get('cycle')
        if c is None:
            continue
        if c not in cycles:
            cycles[c] = {}
        if rec.get('efficiency_index') is not None:
            cycles[c]['efficiency'] = rec['efficiency_index']

    # 3) Autonomy score (current snapshot - assign to latest cycle)
    if AUTONOMY_SCORE.exists():
        try:
            data = json.loads(AUTONOMY_SCORE.read_text(encoding='utf-8'))
            score = data.get('score')
            if score is not None and cycles:
                latest_cycle = max(cycles.keys())
                cycles[latest_cycle]['autonomy'] = score
        except (json.JSONDecodeError, KeyError):
            pass

    # 4) Intervention counts from cycle history
    for rec in load_jsonl(CYCLE_HISTORY):
        c = rec.get('cycle')
        if c is None:
            continue
        if c not in cycles:
            cycles[c] = {}
        if rec.get('intervention_count') is not None:
            cycles[c]['intervention'] = rec['intervention_count']

    return cycles


def compute_velocities(cycles):
    """Compute per-metric velocity across sorted cycles. Returns {metric: [(cycle, velocity), ...]}"""
    sorted_cycles = sorted(cycles.keys())
    velocities = {'autonomy': [], 'efficiency': [], 'intervention': []}

    for i in range(1, len(sorted_cycles)):
        prev_c, curr_c = sorted_cycles[i-1], sorted_cycles[i]
        for metric in METRIC_DIRECTION:
            if metric in cycles[prev_c] and metric in cycles[curr_c]:
                delta = cycles[curr_c][metric] - cycles[prev_c][metric]
                velocities[metric].append((curr_c, delta))

    return velocities


def detect_deceleration(velocities):
    """Detect metrics worsening for 2+ consecutive transitions. Returns list of alert dicts."""
    alerts = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for metric, vel_list in velocities.items():
        if len(vel_list) < 2:
            continue
        higher_is_better = METRIC_DIRECTION[metric]

        consecutive_worsen = 0
        last_delta = 0
        for cycle, delta in vel_list:
            worsening = (delta < 0) if higher_is_better else (delta > 0)
            if worsening:
                consecutive_worsen += 1
                last_delta = delta
            else:
                consecutive_worsen = 0

            if consecutive_worsen >= 2:
                alerts.append({
                    'ts': now,
                    'metric': metric,
                    'velocity_trend': f'worsening for {consecutive_worsen} consecutive cycles (last cycle: {cycle})',
                    'recommended_action': _recommend(metric),
                    'severity': 'warning' if consecutive_worsen == 2 else 'critical',
                })
                break

    return alerts


def _recommend(metric):
    actions = {
        'autonomy': 'Review intervention patterns; check scheduled tasks; verify goal lifecycle automation.',
        'efficiency': 'Check cycle duration trends; review pass budget allocation; reduce rework loops.',
        'intervention': 'Reduce human touchpoints: automate approvals, improve self-healing coverage.',
    }
    return actions.get(metric, 'Investigate metric trend.')


def write_alerts(alerts):
    if not alerts:
        return 0
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_PATH, 'a', encoding='utf-8') as f:
        for a in alerts:
            f.write(json.dumps(a) + '\n')
    return len(alerts)


def run_check():
    cycles = collect_metrics()
    if not cycles:
        print('No cycle data available. Nothing to check.')
        return 0

    velocities = compute_velocities(cycles)
    alerts = detect_deceleration(velocities)
    written = write_alerts(alerts)

    print(f'Cycles analyzed: {sorted(cycles.keys())}')
    for metric, vel_list in velocities.items():
        if vel_list:
            deltas = [f'c{c}:{d:+.2f}' for c, d in vel_list]
            print(f'  {metric}: {" | ".join(deltas)}')
        else:
            print(f'  {metric}: insufficient data (<2 cycles with values)')

    if alerts:
        print(f'ALERTS FIRED: {len(alerts)}')
        for a in alerts:
            print(f'  [{a["severity"]}] {a["metric"]}: {a["velocity_trend"]}')
    else:
        print('No deceleration detected.')
    return written


def selftest():
    """Verify alert logic with synthetic data."""
    passed = 0
    failed = 0

    # Test 1: Decelerating metrics should fire alerts
    cycles_decel = {
        10: {'autonomy': 90, 'efficiency': 80, 'intervention': 2},
        15: {'autonomy': 85, 'efficiency': 78, 'intervention': 3},
        16: {'autonomy': 80, 'efficiency': 75, 'intervention': 4},
    }
    v = compute_velocities(cycles_decel)
    alerts = detect_deceleration(v)
    alert_metrics = [a['metric'] for a in alerts]
    if 'autonomy' in alert_metrics and 'efficiency' in alert_metrics and 'intervention' in alert_metrics:
        passed += 1
        print('  PASS: deceleration detected on all 3 metrics')
    else:
        failed += 1
        print(f'  FAIL: expected all 3 alerts, got {alert_metrics}')

    # Test 2: Steady state should NOT fire alert
    cycles_steady = {
        10: {'autonomy': 80, 'efficiency': 75, 'intervention': 3},
        15: {'autonomy': 80, 'efficiency': 75, 'intervention': 3},
        16: {'autonomy': 80, 'efficiency': 75, 'intervention': 3},
    }
    v = compute_velocities(cycles_steady)
    alerts = detect_deceleration(v)
    if len(alerts) == 0:
        passed += 1
        print('  PASS: no alert on steady data')
    else:
        failed += 1
        print(f'  FAIL: unexpected alerts on steady data: {[a["metric"] for a in alerts]}')

    # Test 3: Accelerating should NOT fire alert
    cycles_accel = {
        10: {'autonomy': 70, 'efficiency': 60, 'intervention': 5},
        15: {'autonomy': 80, 'efficiency': 70, 'intervention': 4},
        16: {'autonomy': 90, 'efficiency': 80, 'intervention': 3},
    }
    v = compute_velocities(cycles_accel)
    alerts = detect_deceleration(v)
    if len(alerts) == 0:
        passed += 1
        print('  PASS: no alert on accelerating data')
    else:
        failed += 1
        print(f'  FAIL: unexpected alerts on accelerating data: {[a["metric"] for a in alerts]}')

    # Test 4: Single cycle dip (recovers) should NOT fire (need 2+ consecutive)
    cycles_single = {
        10: {'autonomy': 90, 'efficiency': 80, 'intervention': 2},
        15: {'autonomy': 85, 'efficiency': 78, 'intervention': 3},
        16: {'autonomy': 88, 'efficiency': 80, 'intervention': 2},
    }
    v = compute_velocities(cycles_single)
    alerts = detect_deceleration(v)
    if len(alerts) == 0:
        passed += 1
        print('  PASS: no alert on single-cycle dip (recovers)')
    else:
        failed += 1
        print(f'  FAIL: unexpected alert on single dip: {[a["metric"] for a in alerts]}')

    # Test 5: Alert format matches expected schema
    cycles_decel = {
        10: {'autonomy': 90, 'efficiency': 80, 'intervention': 2},
        15: {'autonomy': 85, 'efficiency': 78, 'intervention': 3},
        16: {'autonomy': 80, 'efficiency': 75, 'intervention': 4},
    }
    v = compute_velocities(cycles_decel)
    alerts = detect_deceleration(v)
    if alerts:
        a = alerts[0]
        required_keys = {'ts', 'metric', 'velocity_trend', 'recommended_action'}
        if required_keys.issubset(a.keys()):
            passed += 1
            print('  PASS: alert format has required keys')
        else:
            failed += 1
            print(f'  FAIL: missing keys {required_keys - set(a.keys())}')
    else:
        failed += 1
        print('  FAIL: no alerts generated for format test')

    print(f'\nSelftest: {passed}/5 PASS, {failed}/5 FAIL')
    return failed == 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        run_check()
