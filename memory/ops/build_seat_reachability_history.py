#!/usr/bin/env python
"""Convert model-load.jsonl -> seat-reachability-history.jsonl.

Reads per-probe seat state from memory/ops/model-load.jsonl and produces
one line per (seat, day) with {ts, seat, state} format for use by
Researcher's seat_unavailability_v2.py backtest.

Logic: a seat is "available" on a day if ANY probe that day shows it
relocated (on another host). A seat is "unavailable" only if ALL probes
that day show it missing with not_loaded/unreachable and no relocation.

Usage: python memory/ops/build_seat_reachability_history.py
Output: memory/ops/seat-reachability-history.jsonl (append-safe, deduped by ts+seat)
"""
import pathlib, json
from datetime import datetime, date
from collections import defaultdict

SRC = pathlib.Path('memory/ops/model-load.jsonl')
DST = pathlib.Path('memory/ops/seat-reachability-history.jsonl')

def main():
    lines = SRC.read_text(encoding='utf-8').strip().split('\n')
    
    # seat -> day -> best_state (1=available, 0=unavailable)
    seat_day = defaultdict(dict)
    
    for line in lines:
        try:
            rec = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        ts_str = rec.get('ts', '')
        try:
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            d = dt.date()
        except ValueError:
            continue
        
        missing = rec.get('missing', {})
        relocated = rec.get('relocated', {})
        
        for seat in set(missing.keys()) | set(relocated.keys()):
            if seat in relocated:
                # Relocated = available
                prev = seat_day[seat].get(d, 1)
                seat_day[seat][d] = max(prev, 1)
            elif seat in missing:
                state = missing[seat]
                if state in ('not_loaded', 'unreachable'):
                    # Only mark unavailable if no prior probe said available
                    if d not in seat_day[seat]:
                        seat_day[seat][d] = 0
    
    # Write output (full rewrite for idempotency)
    with DST.open('w', encoding='utf-8') as f:
        for seat in sorted(seat_day.keys()):
            for d in sorted(seat_day[seat].keys()):
                state_num = seat_day[seat][d]
                entry = {
                    'ts': d.isoformat(),
                    'seat': seat,
                    'state': 'available' if state_num == 1 else 'unavailable'
                }
                f.write(json.dumps(entry) + '\n')
    
    # Summary
    total = sum(len(v) for v in seat_day.values())
    unavail = sum(1 for v in seat_day.values() for x in v.values() if x == 0)
    print(f"WROTE {DST} ({total} entries, {unavail} unavailable)")
    print(f"Seats: {len(seat_day)}, Days: {len(set(d for v in seat_day.values() for d in v))}")

if __name__ == '__main__':
    main()
