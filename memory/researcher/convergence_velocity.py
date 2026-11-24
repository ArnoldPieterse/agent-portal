"""
convergence_velocity.py - Convergence Velocity Metric
For each completed cycle, compute: goals_closed / total_passes_used = velocity.
Track trend across cycles. Flag if velocity declining >2 consecutive cycles.
Output: memory/ops/velocity-trend.json
"""
import json
import pathlib
from datetime import datetime, timezone, timedelta
from collections import defaultdict

CLOSED_TOPICS = pathlib.Path('memory/goals/closed_topics.json')
AUTOCLOOP = pathlib.Path('memory/ops/autoloop.jsonl')
OUTPUT = pathlib.Path('memory/ops/velocity-trend.json')
DECLINE_THRESHOLD = 2  # flag if declining for >2 consecutive cycles


def load_closed_by_date() -> dict:
    """Load closed topics grouped by date as cycle proxy."""
    if not CLOSED_TOPICS.exists():
        return {}
    try:
        topics = json.loads(CLOSED_TOPICS.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, TypeError):
        return {}
    
    by_date = defaultdict(int)
    for t in topics:
        date = t.get('at', '')
        if date and len(date) >= 10:  # YYYY-MM-DD
            by_date[date[:10]] += 1
    return dict(by_date)


def load_passes_by_date() -> dict:
    """Load autoloop passes grouped by date."""
    if not AUTOCLOOP.exists():
        return {}
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)  # last 30 days
    by_date = defaultdict(int)
    for line in AUTOCLOOP.read_text(encoding='utf-8').strip().split('\n'):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts_str = r.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue
        if ts >= cutoff:
            by_date[ts.strftime('%Y-%m-%d')] += 1
    return dict(by_date)


def compute_velocity(closed_by_date: dict, passes_by_date: dict) -> list:
    """Compute velocity for each cycle (day)."""
    # Get all dates that have either closures or passes
    all_dates = sorted(set(list(closed_by_date.keys()) + list(passes_by_date.keys())))
    
    trend = []
    for date in all_dates:
        goals_closed = closed_by_date.get(date, 0)
        total_passes = passes_by_date.get(date, 0)
        velocity = round(goals_closed / total_passes, 3) if total_passes > 0 else None
        trend.append({
            'date': date,
            'goals_closed': goals_closed,
            'total_passes': total_passes,
            'velocity': velocity
        })
    
    return trend


def detect_decline(trend: list, threshold: int = DECLINE_THRESHOLD) -> dict:
    """Detect if velocity is declining for >threshold consecutive cycles."""
    # Filter to entries with non-null velocity
    valid = [t for t in trend if t['velocity'] is not None]
    if len(valid) < threshold + 1:
        return {'declining': False, 'consecutive_declines': 0, 'detail': f'Insufficient data ({len(valid)} cycles with velocity)'}
    
    consecutive = 0
    max_consecutive = 0
    for i in range(1, len(valid)):
        if valid[i]['velocity'] < valid[i-1]['velocity']:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0
    
    return {
        'declining': max_consecutive > threshold,
        'consecutive_declines': max_consecutive,
        'threshold': threshold,
        'detail': f"Max consecutive declines: {max_consecutive} (threshold: {threshold})"
    }


def main():
    closed = load_closed_by_date()
    passes = load_passes_by_date()
    trend = compute_velocity(closed, passes)
    decline = detect_decline(trend)
    
    result = {
        '_meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'window': 'last 30 days',
            'cycles_analyzed': len(trend),
            'note': 'velocity = goals_closed / total_passes; null when no pass data'
        },
        'trend': trend,
        'decline_flag': decline
    }
    
    OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Wrote {OUTPUT}")
    print(f"  Cycles analyzed: {len(trend)}")
    for t in trend[-5:]:
        v = f"{t['velocity']}" if t['velocity'] is not None else 'N/A'
        print(f"  {t['date']}: {t['goals_closed']} goals / {t['total_passes']} passes = velocity {v}")
    print(f"  Decline flag: {decline['declining']} ({decline['detail']})")


def self_test():
    """Verify: computes correct per-cycle velocity; decline flag triggers on synthetic declining data."""
    # Synthetic: 5 cycles with declining velocity
    closed = {'2026-11-20': 10, '2026-11-21': 8, '2026-11-22': 6, '2026-11-23': 4, '2026-11-24': 2}
    passes = {'2026-11-20': 10, '2026-11-21': 10, '2026-11-22': 10, '2026-11-23': 10, '2026-11-24': 10}
    
    trend = compute_velocity(closed, passes)
    assert len(trend) == 5, f"Expected 5 cycles, got {len(trend)}"
    
    # Verify velocities: 1.0, 0.8, 0.6, 0.4, 0.2
    expected = [1.0, 0.8, 0.6, 0.4, 0.2]
    for i, t in enumerate(trend):
        assert abs(t['velocity'] - expected[i]) < 0.01, f"Cycle {i}: expected {expected[i]}, got {t['velocity']}"
    
    # Decline flag: 4 consecutive declines > threshold of 2
    decline = detect_decline(trend)
    assert decline['declining'] == True, f"Expected declining=True, got {decline}"
    assert decline['consecutive_declines'] == 4, f"Expected 4 consecutive, got {decline['consecutive_declines']}"
    
    # Non-declining test
    closed2 = {'2026-11-20': 5, '2026-11-21': 8, '2026-11-22': 10}
    passes2 = {'2026-11-20': 10, '2026-11-21': 10, '2026-11-22': 10}
    trend2 = compute_velocity(closed2, passes2)
    decline2 = detect_decline(trend2)
    assert decline2['declining'] == False, f"Expected declining=False, got {decline2}"
    
    print("SELF-TEST PASSED: velocity computation correct; decline flag triggers on 4-consecutive-decline data")


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        self_test()
    else:
        main()
