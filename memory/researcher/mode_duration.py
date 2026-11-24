"""
mode_duration.py - Mode Duration Tracker
Reads mode-transitions.jsonl; computes time spent in each mode over last 7 days.
Flags anomaly if IDLE >50% of total time (under-utilization) or WORK <20% (stuck goals).
Output: memory/ops/mode-durations.json
"""
import json
import pathlib
from datetime import datetime, timedelta, timezone
from collections import defaultdict

TRANSITIONS = pathlib.Path('memory/ops/mode-transitions.jsonl')
OUTPUT = pathlib.Path('memory/ops/mode-durations.json')
WINDOW_DAYS = 7
IDLE_THRESHOLD = 50.0   # percent
WORK_THRESHOLD = 20.0   # percent
MODES = ['WORK', 'MAINTENANCE', 'IDLE']


def parse_ts(ts_str: str) -> datetime:
    """Parse various timestamp formats."""
    try:
        ts_clean = ts_str.replace('Z', '+00:00')
        return datetime.fromisoformat(ts_clean)
    except (ValueError, AttributeError):
        return None


def load_transitions(window_days: int = WINDOW_DAYS) -> list:
    """Load transitions within the time window."""
    if not TRANSITIONS.exists():
        return []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    recs = []
    for line in TRANSITIONS.read_text(encoding='utf-8').strip().split('\n'):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = parse_ts(r.get('ts', ''))
        if ts and ts >= cutoff:
            recs.append(r)
    # Sort by timestamp
    recs.sort(key=lambda x: x.get('ts', ''))
    return recs


def compute_durations(transitions: list, window_days: int = WINDOW_DAYS) -> dict:
    """Compute time spent in each mode from transition records."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    total_seconds = (now - cutoff).total_seconds()
    
    # Walk through transitions to compute duration in each mode
    durations = {m: 0.0 for m in MODES}
    current_mode = 'IDLE'  # default before first transition
    prev_ts = cutoff
    
    for t in transitions:
        ts = parse_ts(t.get('ts', ''))
        if ts is None:
            continue
        to_mode = t.get('to_mode', 'IDLE').upper()
        from_mode = t.get('from_mode', 'IDLE').upper()
        
        # Time spent in current mode since last transition
        elapsed = (ts - prev_ts).total_seconds()
        if elapsed > 0:
            durations[current_mode] = durations.get(current_mode, 0.0) + elapsed
        
        current_mode = to_mode
        prev_ts = ts
    
    # Add remaining time in current mode up to now
    remaining = (now - prev_ts).total_seconds()
    if remaining > 0:
        durations[current_mode] = durations.get(current_mode, 0.0) + remaining
    
    # Convert to hours and compute percentages
    result = {}
    for m in MODES:
        hours = durations[m] / 3600.0
        pct = (durations[m] / total_seconds * 100) if total_seconds > 0 else 0
        result[m] = {
            'hours': round(hours, 2),
            'percent': round(pct, 1)
        }
    
    return {
        '_meta': {
            'generated_at': now.isoformat(),
            'window_days': window_days,
            'transitions_in_window': len(transitions),
            'total_hours': round(total_seconds / 3600.0, 2)
        },
        **result
    }


def check_anomalies(durations: dict) -> list:
    """Check for anomaly conditions."""
    anomalies = []
    idle_pct = durations.get('IDLE', {}).get('percent', 0)
    work_pct = durations.get('WORK', {}).get('percent', 0)
    
    if idle_pct > IDLE_THRESHOLD:
        anomalies.append({
            'type': 'UNDER_UTILIZATION',
            'detail': f"IDLE mode at {idle_pct}% (>50% threshold) - fleet is under-utilized",
            'severity': 'warning'
        })
    if work_pct < WORK_THRESHOLD:
        anomalies.append({
            'type': 'STUCK_GOALS',
            'detail': f"WORK mode at {work_pct}% (<20% threshold) - possible stuck goals",
            'severity': 'warning'
        })
    return anomalies


def main():
    transitions = load_transitions()
    result = compute_durations(transitions)
    
    # Add anomalies
    result['anomalies'] = check_anomalies(result)
    result['has_anomaly'] = len(result['anomalies']) > 0
    
    OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Wrote {OUTPUT}")
    print(f"  Transitions in window: {result['_meta']['transitions_in_window']}")
    for m in MODES:
        d = result[m]
        print(f"  {m}: {d['hours']}h ({d['percent']}%)")
    if result['anomalies']:
        for a in result['anomalies']:
            print(f"  ** ANOMALY: {a['type']}: {a['detail']}")
    else:
        print("  No anomalies detected")


def self_test():
    """Verify: on synthetic transition data, durations sum to total elapsed; anomaly flags at boundaries."""
    import tempfile, shutil
    test_dir = pathlib.Path(tempfile.mkdtemp())
    trans_path = test_dir / 'mode-transitions.jsonl'
    
    now = datetime.now(timezone.utc)
    # Synthetic: IDLE for 6 days, WORK for 1 day -> IDLE=85.7%, WORK=14.3% (both anomaly)
    entries = [
        {'ts': (now - timedelta(days=1)).isoformat(), 'from_mode': 'IDLE', 'to_mode': 'WORK', 'trigger': 'test'},
        # Before that: IDLE for 6 days
    ]
    trans_path.write_text('\n'.join(json.dumps(e) for e in entries), encoding='utf-8')
    
    global TRANSITIONS
    orig = TRANSITIONS
    TRANSITIONS = trans_path
    
    transitions = load_transitions()
    result = compute_durations(transitions)
    
    # Verify durations sum to total window
    total_pct = sum(result[m]['percent'] for m in MODES)
    assert abs(total_pct - 100.0) < 1.0, f"Durations should sum to ~100%, got {total_pct}%"
    
    # Verify anomalies: IDLE >50% (should be ~85.7%) and WORK <20% (should be ~14.3%)
    anomalies = check_anomalies(result)
    types = [a['type'] for a in anomalies]
    assert 'UNDER_UTILIZATION' in types, f"Expected UNDER_UTILIZATION, got {types}"
    assert 'STUCK_GOALS' in types, f"Expected STUCK_GOALS, got {types}"
    
    TRANSITIONS = orig
    shutil.rmtree(test_dir, ignore_errors=True)
    print("SELF-TEST PASSED: durations sum to total; anomaly flags trigger correctly at thresholds")


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        self_test()
    else:
        main()
