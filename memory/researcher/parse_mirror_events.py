"""
parse_mirror_events.py — Researcher goal #3: frequency-table generator.
Reads mirror_events.log (JSONL) and produces:
  1. Count by (kind, dir/trigger)
  2. Top-reverting files (path or file field)
  3. Trigger distribution
  4. Time-bucketed activity (hourly)
Usage: python parse_mirror_events.py [log_path]
Default log path: mirror_events.log in CWD.
"""
import json, sys, os
from collections import Counter, defaultdict
from datetime import datetime

def load_events(path):
    events = []
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Mirror has not run since instrumentation.")
        return None
    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                print(f"WARN: line {i} malformed, skipped")
                continue
            if ev.get('_test'):
                continue  # skip smoke-test events
            events.append(ev)
    return events

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'mirror_events.log'
    events = load_events(path)
    if events is None:
        sys.exit(0)
    if not events:
        print("No live events (only test data or empty). Waiting for mirror to run.")
        sys.exit(0)

    print(f"=== MIRROR EVENTS ANALYSIS ({len(events)} live events) ===")
    print(f"Log: {path}")
    ts = [ev['t'] for ev in events if 't' in ev]
    print(f"Time range: {min(ts)} -> {max(ts)}")
    print()

    # 1. Count by kind + dir/trigger
    kind_dir = Counter()
    for ev in events:
        kind = ev.get('kind', 'unknown')
        sub = ev.get('dir', ev.get('trigger', '?'))
        kind_dir[(kind, sub)] += 1
    print("--- Events by (kind, dir/trigger) ---")
    for (k, s), c in kind_dir.most_common():
        print(f"  {k:8s} / {s:12s}: {c}")
    print()

    # 2. Top-reverting files
    path_counter = Counter()
    for ev in events:
        p = ev.get('path', ev.get('file', '?'))
        path_counter[p] += 1
    print("--- Top files by event count ---")
    for p, c in path_counter.most_common(15):
        print(f"  {p:40s}: {c}")
    print()

    # 3. Trigger distribution (for reverts)
    trigger_c = Counter()
    for ev in events:
        if ev.get('kind') == 'revert':
            trigger_c[ev.get('trigger', 'unknown')] += 1
    print("--- Revert triggers ---")
    for t, c in trigger_c.most_common():
        print(f"  {t:20s}: {c}")
    print()

    # 4. Hourly activity
    hourly = Counter()
    for ev in events:
        if 't' in ev:
            try:
                dt = datetime.strptime(ev['t'], '%Y-%m-%d %H:%M:%S')
                hourly[dt.strftime('%Y-%m-%d %H:00')] += 1
            except ValueError:
                pass
    print("--- Hourly event counts ---")
    for h, c in sorted(hourly.items()):
        bar = '#' * min(c, 40)
        print(f"  {h}: {c:3d} {bar}")

if __name__ == '__main__':
    main()